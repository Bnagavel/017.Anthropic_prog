"""
discord_mailbox.py — 24/7 Local File Mailbox <-> Discord Mobile Relay + CLI Executor.

Supports:
  - Continuous non-blocking polling of both `logs/outbox.json` and Discord channel messages
  - Rich Status Embeds (`type: "embed"`) + optional attached PNG mesh preview (`image_path`)
  - Direct Image/File Uploads (`type: "file"`)
  - CLI Worker Execution (`type: "cli_exec"` / `"claude_exec"`) for `claude.cmd` (haiku/sonnet/opus)
    and `gemini.cmd` (flash-lite/flash/pro), with automatic quota/availability check & fallback prompt!
  - Automatic hot-reload when `discord_mailbox.py`, `discord_gate.py`, or `model_router.py` is updated!
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, Dict, Optional

from discord_gate import (
    DISCORD_API_BASE,
    _discord_request,
    _get_discord_creds,
    get_latest_message_id,
    load_env_file,
    send_file_message,
    send_status_embed,
    send_text_message,
)
from model_router import (
    MODEL_POOL,
    QUOTA_ERROR_PATTERNS,
    ModelRouter,
    build_cli_command,
    find_step_model_by_chat,
)
from daily_orchestrator import (
    format_queue_summary,
    load_queue,
    select_next_item,
)


LOOP_DIR = Path(__file__).resolve().parent
LOGS_DIR = LOOP_DIR / "logs"
OUTBOX_FILE = LOGS_DIR / "outbox.json"
INBOX_FILE = LOGS_DIR / "inbox.json"
WATCHED_FILES = [
    LOOP_DIR / "discord_mailbox.py",
    LOOP_DIR / "discord_gate.py",
    LOOP_DIR / "model_router.py",
]


def _get_mtimes() -> Dict[str, float]:
    return {str(p): (p.stat().st_mtime if p.exists() else 0.0) for p in WATCHED_FILES}


def _read_json(path: Path) -> Optional[Dict[str, Any]]:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def _write_json(path: Path, data: Dict[str, Any]) -> None:
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    tmp.replace(path)


def _poll_discord_once(after_id: Optional[str]) -> tuple[Optional[str], Optional[str]]:
    """Non-blocking check for any new user message in the Discord channel after `after_id`."""
    bot_token, channel_id, _ = _get_discord_creds()
    if not (bot_token and channel_id):
        return None, after_id

    try:
        query = "?limit=10"
        if after_id:
            query += f"&after={urllib.parse.quote(str(after_id))}"
        url = f"{DISCORD_API_BASE}/channels/{channel_id}/messages{query}"
        messages = _discord_request("GET", url, bot_token=bot_token)

        last_seen = after_id
        if isinstance(messages, list) and messages:
            for msg in reversed(messages):
                msg_id = str(msg.get("id", ""))
                if msg_id:
                    last_seen = msg_id
                if msg.get("author", {}).get("bot"):
                    continue
                content = (msg.get("content") or "").strip()
                attachments = msg.get("attachments") or []
                att_paths = []
                for idx, att in enumerate(attachments):
                    att_url = att.get("url")
                    if not att_url:
                        continue
                    try:
                        from discord_gate import USER_AGENT
                        ext = Path(att.get("filename", "img.png")).suffix or ".png"
                        out_p = LOGS_DIR / f"user_sketch_{msg_id}_{idx}{ext}"
                        req = urllib.request.Request(att_url, headers={"User-Agent": USER_AGENT})
                        with urllib.request.urlopen(req, timeout=20) as resp:
                            out_p.write_bytes(resp.read())
                        att_paths.append(str(out_p))
                    except Exception as att_exc:
                        print(f"[DISCORD ATTACHMENT WARN] {att_exc}")
                if att_paths:
                    att_note = "\n".join(f"[ATTACHMENT: {p}]" for p in att_paths)
                    content = f"{content}\n{att_note}".strip()
                if content:
                    return content, last_seen
        return None, last_seen
    except Exception as exc:
        print(f"[DISCORD POLL] Warning: {exc}")
        return None, after_id


def _execute_cli_worker(outbox: Dict[str, Any], req_id: str) -> Optional[str]:
    """Run a CLI worker (`claude.cmd` or `gemini.cmd`) and check availability/quota."""
    router = ModelRouter.load()
    alias = outbox.get("model_alias") or outbox.get("model", "claude-sonnet")
    if alias in ("haiku", "sonnet", "opus"):
        alias = f"claude-{alias}"

    complexity = float(outbox.get("complexity", 0.4))
    avail, avail_reason = router.check_availability(alias)
    if not avail:
        next_spec = router.get_next_available_model(alias, complexity)
        router.last_suggested_fallback = next_spec.alias
        router.save()
        return send_text_message(
            f"⚠️ **Requested model `{alias}` is unavailable** ({avail_reason}).\n"
            f"👉 **Suggested next model:** **`{next_spec.alias}`** (`{next_spec.model_flag}`).\n"
            f"Reply **`NEXT_MODEL`** (or **`use {next_spec.alias}`**) to move on to the next model!"
        )

    spec = MODEL_POOL[alias]
    cwd_path = outbox.get("cwd", "<WORKSPACE>/")
    prompt_text = outbox.get("prompt", "")
    summary = outbox.get("summary", "Executing task")
    task_pattern = outbox.get("task_pattern", "general")
    cad_model_id = outbox.get("cad_model_id", "")

    send_text_message(
        f"🏷️ **AutoHex Dispatcher ({router.router_model}) → `{spec.alias}`** (`{spec.model_flag}` | timeout `{spec.timeout_sec}s` | complexity `{complexity:.2f}`)\n"
        f"⚙️ _{summary}_..."
    )

    cmd = build_cli_command(spec, prompt_text, str(cwd_path))
    print(f"[CLI WORKER] Running {spec.alias} (timeout={spec.timeout_sec}s): {' '.join(cmd[:6])} ...")

    t0 = time.time()
    timed_out = False
    try:
        proc = subprocess.run(
            cmd,
            cwd=str(cwd_path),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=spec.timeout_sec,
        )
        out_text = ((proc.stdout or "") + "\n" + (proc.stderr or "")).strip()
    except subprocess.TimeoutExpired as exc:
        timed_out = True
        out_str = exc.stdout.decode("utf-8", errors="replace") if isinstance(exc.stdout, bytes) else (exc.stdout or "")
        err_str = exc.stderr.decode("utf-8", errors="replace") if isinstance(exc.stderr, bytes) else (exc.stderr or "")
        out_text = (out_str + "\n" + err_str + f"\n[TIMEOUT after {spec.timeout_sec}s]").strip()
        proc = None
    except Exception as exc:
        out_text = str(exc)
        proc = None

    elapsed = round(time.time() - t0, 2)
    lower_out = out_text.lower()
    hit_quota = any(pat in lower_out for pat in QUOTA_ERROR_PATTERNS)
    failed = timed_out or proc is None or proc.returncode != 0 or hit_quota

    out_log = LOGS_DIR / f"worker_{spec.alias}_{req_id}.md"
    out_log.write_text(out_text, encoding="utf-8")

    escalation_note = router.record_telemetry(
        alias=spec.alias,
        task_pattern=task_pattern,
        elapsed_sec=elapsed,
        success=not failed,
        timed_out=timed_out,
        cad_model_id=cad_model_id,
    )

    if failed:
        reason = (
            f"Timed out after {spec.timeout_sec}s"
            if timed_out
            else ("Quota/rate limit reached" if hit_quota else f"CLI exited with code {getattr(proc, 'returncode', -1)}")
        )
        router.mark_unavailable(spec.alias, cooldown_minutes=45 if hit_quota else 10, reason=reason)
        next_spec = router.get_next_available_model(spec.alias, min(1.0, complexity + 0.25))
        router.last_suggested_fallback = next_spec.alias
        router.save()
        err_preview = out_text[:450]
        esc_line = f"\n{escalation_note}\n" if escalation_note else "\n"
        return send_text_message(
            f"⚠️ **Model `{spec.alias}` stopped ({reason} in `{elapsed:.1f}s`)**:\n"
            f"```text\n{err_preview}\n```"
            f"{esc_line}"
            f"👉 **Suggested next model (escalated):** **`{next_spec.alias}`** (`{next_spec.model_flag}`, timeout `{next_spec.timeout_sec}s`).\n"
            f"Reply **`NEXT_MODEL`** (or **`use {next_spec.alias}`**) to move on immediately!"
        )

    preview = out_text[:1400] + ("..." if len(out_text) > 1400 else "")
    esc_line = f"\n\n{escalation_note}" if escalation_note else ""
    return send_text_message(
        f"✅ **Executed by `{spec.alias}` (`{spec.model_flag}` in `{elapsed:.1f}s`/{spec.timeout_sec}s):**\n"
        f"{preview}{esc_line}\n\n"
        "💬 _Reply `PROCEED` / `NEXT` / `MODELS` or any follow-up instruction on Discord!_"
    )


def _execute_host_py(outbox: Dict[str, Any], req_id: str) -> None:
    """Run a Python command/script using 010.AutoHex venv on the host and write output to inbox.json."""
    venv_py = Path(r"<WORKSPACE>/.venv\Scripts\python.exe")
    py_exe = str(venv_py) if venv_py.exists() else sys.executable
    cmd = outbox.get("cmd") or [py_exe, str(outbox.get("script", ""))]
    cwd = outbox.get("cwd", r"<WORKSPACE>/")
    timeout_sec = int(outbox.get("timeout_sec", 90))
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONPATH"] = r"<WORKSPACE>/src"

    print(f"[HOST_PY] Running on host: {cmd} (timeout={timeout_sec}s)...")
    try:
        proc = subprocess.run(
            cmd,
            cwd=cwd,
            env=env,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout_sec,
        )
        reply_text = f"RC={proc.returncode}\n{proc.stdout}\n{proc.stderr}".strip()
    except subprocess.TimeoutExpired:
        reply_text = f"RC=124\nTIMEOUT after {timeout_sec}s"
    except Exception as exc:
        reply_text = f"RC=1\nERROR: {exc}"

    _write_json(
        INBOX_FILE,
        {
            "request_id": req_id,
            "reply": reply_text,
            "discord_msg_id": "host_py",
            "timestamp": time.time(),
        },
    )


def _safe_send_text(text: str) -> Optional[str]:
    try:
        return send_text_message(text)
    except Exception as exc:
        print(f"[DISPATCH SEND WARN] {exc}")
        return None


def _handle_incoming_discord_message(user_reply: str, current_req_id: str) -> tuple[Optional[str], Optional[Dict[str, Any]]]:
    """Process incoming Discord message immediately through the Gemini 3.8 Flash Dispatcher."""
    clean = user_reply.strip()
    cmd_upper = clean.upper()

    router = ModelRouter.load()
    queue_data = load_queue()
    current_item = select_next_item(queue_data) or {"id": "p2_shaft_coupling", "phase": "phase_2", "metrics": {}}
    metrics = current_item.get("metrics", {})

    # 1. Quick command: STOP
    if cmd_upper in ("STOP", "EXIT", "QUIT"):
        sent_id = _safe_send_text("👋 Discord Mailbox Relay stopped.")
        return sent_id, {"action": "stop"}

    # 2. Quick command: STATUS / QUEUE
    if cmd_upper in ("STATUS", "QUEUE"):
        text = format_queue_summary(queue_data, active_id=current_item.get("id", ""))
        sent_id = _safe_send_text(text)
        return sent_id, {"action": "status"}

    # 3. Quick command: MODELS / ROUTER
    if cmd_upper in ("MODELS", "ROUTER", "MODEL STATUS"):
        sent_id = _safe_send_text(router.format_router_status())
        return sent_id, {"action": "models"}

    # 4. Advance Queue: NEXT / PROCEED / ADVANCE
    if cmd_upper in ("NEXT", "PROCEED", "CONTINUE", "ADVANCE", "GO"):
        next_item = select_next_item(queue_data)
        if not next_item:
            sent_id = _safe_send_text("🎉 All models in queue are passed! Reply `STATUS` or `run <name>` to re-run any model.")
            return sent_id, {"action": "all_passed"}
        text = (
            f"⏩ **Advancing to Model `{next_item['id']}`** (`{next_item['rel_path']}`)\n"
            f"⚙️ Queue updated. Running HexPrep baseline..."
        )
        sent_id = _safe_send_text(text)
        return sent_id, {"action": "advance_next", "model_id": next_item["id"]}

    # 4b. Status inquiries: 'are you still on the last job', 'is it still going on'
    if any(q in clean.lower() for q in ("still on", "still going", "what task", "current job", "last job", "status?")):
        cur_id = current_item.get("id", "none")
        cur_st = current_item.get("status", "unknown")
        text = (
            f"ℹ️ **Current Job Status**:\n"
            f"- Model: **`{cur_id}`** (`{current_item.get('rel_path', '')}`)\n"
            f"- Status: `{cur_st.upper()}`\n"
            f"💡 Reply **`NEXT`** or **`PROCEED`** to advance to the next model in queue!"
        )
        sent_id = _safe_send_text(text)
        return sent_id, {"action": "query_job"}

    # 4c. CAD model switching: 'run <step_name>', 'load <step_name>'
    switched = find_step_model_by_chat(queue_data, clean)
    if switched:
        text = f"📂 Switching active CAD model to **`{switched['id']}`** (`{switched['rel_path']}`)."
        sent_id = _safe_send_text(text)
        return sent_id, {"action": "switch_cad", "model_id": switched["id"]}

    # 5. Dispatch task or model selection through Router (Gemini 3.8 Flash)
    decision = router.dispatch("code_fix", current_item, metrics, user_text=clean)

    # 5a. Explicit model switch command (e.g. 'use sonnet', 'model auto', or unavailable warning)
    if decision.discord_notice and not decision.cleaned_task_text:
        sent_id = _safe_send_text(decision.discord_notice)
        return sent_id, {"action": "model_switch", "alias": decision.chosen_model.alias if decision.chosen_model else None}

    # 5b. Task / Feedback message (e.g. cross bore / shaft bore refinement)
    if not decision.ok:
        sent_id = _safe_send_text(decision.discord_notice)
        return sent_id, {"action": "unavailable"}

    chosen = decision.chosen_model
    preview = clean.split("\n")[0][:180] + ("..." if len(clean.split("\n")[0]) > 180 else "")
    ack_text = (
        f"🧭 **AutoHex Dispatcher ({router.router_model})**\n"
        f"📥 **Received Directive** for `{current_item.get('id', 'CAD')}`:\n"
        f"> _{preview}_\n\n"
        f"⚡ **Auto-Routed to**: **`{chosen.alias}`** (`{chosen.model_flag}` | Tier {chosen.tier} | Complexity `{decision.complexity:.2f}`)\n"
        f"💡 **Rationale**: {decision.rationale}\n"
        f"⚙️ **Status**: Active worker engaged. Router will automatically revert to **{router.router_model}** once task finishes."
    )
    sent_id = _safe_send_text(ack_text)

    decision_dict = {
        "ok": True,
        "alias": chosen.alias,
        "provider": chosen.provider,
        "cli_bin": chosen.cli_bin,
        "model_flag": chosen.model_flag,
        "tier": chosen.tier,
        "timeout_sec": chosen.timeout_sec,
        "complexity": decision.complexity,
        "task_pattern": decision.task_pattern,
        "rationale": decision.rationale,
        "cleaned_task_text": decision.cleaned_task_text,
    }
    return sent_id, decision_dict


def main() -> None:
    load_env_file()
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    initial_mtimes = _get_mtimes()

    print("==========================================================")
    print("  AutoHex Discord Mailbox Relay — ACTIVE (v4 Dispatcher)")
    print("  Watching: logs/outbox.json  ->  Discord Mobile & CLI Workers")
    print("  Relaying: Discord Mobile    ->  logs/inbox.json (24/7)")
    print("==========================================================")

    outbox_init = _read_json(OUTBOX_FILE)
    inbox_init = _read_json(INBOX_FILE)
    current_req_id = str(outbox_init.get("request_id", "")) if outbox_init else ""
    last_discord_msg_id = None
    if outbox_init and outbox_init.get("discord_msg_id"):
        last_discord_msg_id = str(outbox_init.get("discord_msg_id"))
    elif inbox_init and inbox_init.get("discord_msg_id") and str(inbox_init.get("discord_msg_id")).isdigit():
        last_discord_msg_id = str(inbox_init.get("discord_msg_id"))
    else:
        try:
            last_discord_msg_id = get_latest_message_id()
        except Exception as exc:
            print(f"[STARTUP] Initial Discord poll skipped ({exc}); continuing into main loop...")

    last_poll_ts = 0.0
    consecutive_errors = 0
    max_retries = 3

    while True:
        try:
            # 1. Auto-reload if script files were updated on disk
            if _get_mtimes() != initial_mtimes:
                print("\n[HOT-RELOAD] Detected update to mailbox/dispatcher code — restarting relay in-place...")
                sys.exit(subprocess.call([sys.executable] + sys.argv))

            # 2. Check outbox.json for any undelivered message from Antigravity
            outbox = _read_json(OUTBOX_FILE)
            if outbox:
                req_id = str(outbox.get("request_id", ""))
                if req_id:
                    current_req_id = req_id

                if not outbox.get("delivered"):
                    msg_type = outbox.get("type", "text")
                    print(f"\n[OUTBOX -> DISCORD] Processing {msg_type} (request_id={req_id})...")

                    sent_id = None
                    try:
                        if msg_type == "embed":
                            sent_id = send_status_embed(
                                title=outbox.get("title", "AutoHex Status"),
                                model_rel_path=outbox.get("model_rel_path", ""),
                                status=outbox.get("status", ""),
                                metrics=outbox.get("metrics", {}),
                                gemini_spec_summary=outbox.get("spec_summary", ""),
                                color=int(outbox.get("color", 0x2ECC71)),
                            )
                            img_path = outbox.get("image_path")
                            if img_path and Path(img_path).exists():
                                file_id = send_file_message(Path(img_path), outbox.get("image_caption", ""))
                                if file_id:
                                    sent_id = file_id
                        elif msg_type == "file":
                            img_path = outbox.get("image_path", "")
                            sent_id = send_file_message(Path(img_path), outbox.get("message", ""))
                        elif msg_type in ("claude_exec", "cli_exec"):
                            sent_id = _execute_cli_worker(outbox, req_id)
                        elif msg_type == "host_py":
                            _execute_host_py(outbox, req_id)
                            sent_id = None
                        else:
                            sent_id = send_text_message(outbox.get("message", ""))

                        consecutive_errors = 0
                    except Exception as exc:
                        consecutive_errors += 1
                        print(f"[OUTBOX ERROR] Attempt {consecutive_errors}/{max_retries} failed: {exc}")
                        if consecutive_errors >= max_retries:
                            print(f"[OUTBOX SKIP] Reached max retries ({max_retries}) for request {req_id}. Skipping bad message and keeping relay alive.")
                            outbox["delivered"] = True
                            outbox["error"] = str(exc)
                            _write_json(OUTBOX_FILE, outbox)
                            consecutive_errors = 0
                        time.sleep(3.0)
                        continue

                    if sent_id:
                        last_discord_msg_id = sent_id

                    outbox["delivered"] = True
                    outbox["discord_msg_id"] = sent_id
                    _write_json(OUTBOX_FILE, outbox)
                    print(f"[OUTBOX DELIVERED] Waiting for mobile reply (request_id={req_id})...")

            # 3. Poll Discord every 3 seconds continuously
            now = time.time()
            if (now - last_poll_ts) >= 3.0:
                last_poll_ts = now
                user_reply, last_discord_msg_id = _poll_discord_once(last_discord_msg_id)
                if user_reply:
                    print(f"[INBOX RECEIVED] User replied: {user_reply} (for request_id={current_req_id})")
                    disp_msg_id, decision_dict = _handle_incoming_discord_message(user_reply, current_req_id)
                    if disp_msg_id:
                        last_discord_msg_id = disp_msg_id
                    _write_json(
                        INBOX_FILE,
                        {
                            "request_id": current_req_id,
                            "reply": user_reply,
                            "dispatch_decision": decision_dict,
                            "discord_msg_id": last_discord_msg_id,
                            "timestamp": now,
                        },
                    )
                    if user_reply.strip().upper() in ("STOP", "EXIT", "QUIT"):
                        print("[RELAY] Stop command received. Exiting.")
                        sys.exit(42)
        except KeyboardInterrupt:
            print("\n[RELAY] Interrupted by user. Exiting.")
            break
        except Exception as loop_exc:
            print(f"[LOOP RECOVERED] Transient error caught (keeping relay alive): {loop_exc}")
            time.sleep(3.0)

        time.sleep(1.0)


if __name__ == "__main__":
    main()
