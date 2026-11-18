"""
agy_step.py — Sandboxed Dispatcher & Helper for Option 1 ("Antigravity as the Boss").

Communicates with `discord_mailbox.py` purely via local files (`logs/outbox.json`
and `logs/inbox.json`) so Antigravity NEVER needs network access or PC permission popups!

Commands:
  1. python agy_step.py dispatch --message "<discord_msg>" [--task-type chat|spec|code_fix] [--model-id <id>]
  2. python agy_step.py baseline [--model-id <id>] [--size <mm>]
  3. python agy_step.py wait-embed --model-id <id> --spec-file <path>
  4. python agy_step.py wait-chat --message "<text>" [--image-file <path>]
  5. python agy_step.py cli-exec --model <alias> --prompt-file <path> [--summary "<text>"]
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import time
import uuid
from pathlib import Path
from typing import Any, Dict, Optional

from daily_orchestrator import (
    LOGS_DIR,
    load_queue,
    run_hexprep_baseline,
    save_queue,
    select_next_item,
)
from model_router import ModelRouter


OUTBOX_FILE = LOGS_DIR / "outbox.json"
INBOX_FILE = LOGS_DIR / "inbox.json"


def _write_json(path: Path, data: Dict[str, Any]) -> None:
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    tmp.replace(path)


def _read_json(path: Path) -> Optional[Dict[str, Any]]:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def _send_via_mailbox_and_wait(payload: Dict[str, Any], timeout_sec: int = 86400) -> str:
    req_id = uuid.uuid4().hex[:10]
    payload["request_id"] = req_id
    payload["delivered"] = False
    _write_json(OUTBOX_FILE, payload)
    print(f"[MAILBOX] Queued request_id={req_id} in logs/outbox.json (ensure run_discord_mailbox.bat is running)...")

    start_ts = time.time()
    while (time.time() - start_ts) < timeout_sec:
        inbox = _read_json(INBOX_FILE)
        if inbox and str(inbox.get("request_id")) == req_id:
            return str(inbox.get("reply", "")).strip()
        time.sleep(1.5)

    raise TimeoutError("Timed out waiting for reply in logs/inbox.json")


def cmd_dispatch(args: argparse.Namespace) -> None:
    """Run the AutoHex Dispatcher Layer on an incoming Discord message:
    - Handles manual model selection ("use haiku", "pick opus", "model auto", "NEXT_MODEL")
    - Checks exact model availability; if unavailable, prompts user on Discord to move on to next model!
    - Outputs DISPATCH_DECISION_JSON for the router to delegate to CLI or Subagent.
    """
    queue_data = load_queue()
    item = select_next_item(queue_data, model_id=args.model_id) or {"id": "general", "phase": "phase_1", "metrics": {}}
    metrics = item.get("metrics", {})
    router = ModelRouter.load()

    low = args.message.strip().lower()
    if low in ("models", "router", "model status"):
        reply = _send_via_mailbox_and_wait({"type": "text", "message": router.format_router_status()})
        print(f"DISCORD_USER_REPLY:{reply}")
        return

    decision = router.dispatch(
        task_type=args.task_type,
        item=item,
        metrics=metrics,
        user_text=args.message,
    )

    # Case 1: User asked for a specific model that is NOT available -> notify on Discord & wait to move on!
    if not decision.ok:
        reply = _send_via_mailbox_and_wait({"type": "text", "message": decision.discord_notice})
        print(f"DISCORD_USER_REPLY:{reply}")
        return

    # Case 2: Pure model-switch command ("use haiku", "model auto") with no inline task
    if decision.discord_notice and not decision.cleaned_task_text:
        reply = _send_via_mailbox_and_wait({"type": "text", "message": decision.discord_notice})
        print(f"DISCORD_USER_REPLY:{reply}")
        return

    # Case 3: Ready to execute with chosen worker model
    chosen = decision.chosen_model
    out = {
        "ok": True,
        "alias": chosen.alias,
        "provider": chosen.provider,
        "cli_bin": chosen.cli_bin,
        "model_flag": chosen.model_flag,
        "tier": chosen.tier,
        "timeout_sec": chosen.timeout_sec,
        "slow_threshold_sec": chosen.slow_threshold_sec,
        "complexity": decision.complexity,
        "task_pattern": decision.task_pattern,
        "rationale": decision.rationale,
        "cleaned_task_text": decision.cleaned_task_text,
        "next_fallback": decision.next_suggested_model.alias if decision.next_suggested_model else "agy-flash",
    }
    print("DISPATCH_DECISION_JSON:" + json.dumps(out))


def cmd_baseline(args: argparse.Namespace) -> None:
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    queue_data = load_queue()
    project_root = Path(queue_data["project_root"])
    models_root = Path(queue_data["models_root"])

    item = select_next_item(queue_data, model_id=args.model_id)
    if not item:
        print("QUEUE_EMPTY")
        return

    if args.size:
        item["target_size_mm"] = float(args.size)

    model_id = item["id"]
    rel_path = item["rel_path"]
    step_path = models_root / rel_path
    target_size = float(item.get("target_size_mm", queue_data.get("default_target_size_mm", 1.5)))
    output_msh = LOGS_DIR / f"{model_id}.msh"

    item["status"] = "in_progress"
    item["last_run"] = dt.datetime.now(dt.timezone.utc).isoformat()
    save_queue(queue_data)

    metrics = run_hexprep_baseline(project_root, step_path, target_size, output_msh)
    log_path = LOGS_DIR / f"{model_id}_baseline.log"
    log_path.write_text(metrics.get("raw_log", ""), encoding="utf-8")

    item["metrics"] = {k: v for k, v in metrics.items() if k != "raw_log"}
    if metrics["valid"]:
        item["status"] = "passed"
    save_queue(queue_data)

    router = ModelRouter.load()
    decision = router.dispatch("spec", item, metrics)

    summary = {
        "model_id": model_id,
        "rel_path": rel_path,
        "target_size_mm": target_size,
        "metrics": item["metrics"],
        "complexity": decision.complexity,
        "recommended_worker": decision.chosen_model.alias if decision.chosen_model else "agy-flash",
        "recommended_provider": decision.chosen_model.provider if decision.chosen_model else "antigravity",
        "recommended_flag": decision.chosen_model.model_flag if decision.chosen_model else "flash",
        "rationale": decision.rationale,
        "log_file": str(log_path),
    }
    print("BASELINE_RESULT_JSON:" + json.dumps(summary))


def cmd_wait_embed(args: argparse.Namespace) -> None:
    queue_data = load_queue()
    item = select_next_item(queue_data, model_id=args.model_id)
    if not item:
        raise SystemExit(f"Model {args.model_id} not found")

    metrics = item.get("metrics", {})
    spec_text = Path(args.spec_file).read_text(encoding="utf-8") if args.spec_file else args.spec_text
    status_label = "VALID (Passed)" if metrics.get("valid") else "NEEDS FIX"
    router = ModelRouter.load()

    payload = {
        "type": "embed",
        "title": f"AutoHex ({router.router_model} Dispatcher): {item['id']}",
        "model_rel_path": f"{item['rel_path']} (size={item.get('target_size_mm', 1.5)}mm)",
        "status": status_label,
        "metrics": metrics,
        "spec_summary": spec_text
        + "\n\n💬 **Reply:** `PROCEED` | `NEXT` | `SKIP` | `use haiku/sonnet/opus/flash` | `MODELS`",
        "color": 0x2ECC71 if metrics.get("valid") else 0xE67E22,
    }
    if args.image_file:
        payload["image_path"] = str(Path(args.image_file).resolve())
    reply = _send_via_mailbox_and_wait(payload)
    print(f"DISCORD_USER_REPLY:{reply}")


def cmd_wait_chat(args: argparse.Namespace) -> None:
    text = Path(args.message_file).read_text(encoding="utf-8") if args.message_file else args.message
    if args.image_file:
        payload = {
            "type": "file",
            "image_path": str(Path(args.image_file).resolve()),
            "message": text,
        }
    else:
        payload = {
            "type": "text",
            "message": text,
        }
    reply = _send_via_mailbox_and_wait(payload)
    print(f"DISCORD_USER_REPLY:{reply}")


def cmd_cli_exec(args: argparse.Namespace) -> None:
    queue_data = load_queue()
    prompt_text = Path(args.prompt_file).read_text(encoding="utf-8") if args.prompt_file else args.prompt
    payload = {
        "type": "cli_exec",
        "model_alias": args.model,
        "complexity": args.complexity,
        "task_pattern": args.task_pattern,
        "cad_model_id": args.cad_model_id,
        "cwd": args.cwd or queue_data.get("project_root", "<WORKSPACE>/"),
        "summary": args.summary,
        "prompt": prompt_text,
    }
    reply = _send_via_mailbox_and_wait(payload)
    print(f"DISCORD_USER_REPLY:{reply}")


def cmd_record_telemetry(args: argparse.Namespace) -> None:
    router = ModelRouter.load()
    note = router.record_telemetry(
        alias=args.model,
        task_pattern=args.task_pattern,
        elapsed_sec=args.elapsed,
        success=not args.failed,
        timed_out=args.timed_out,
        cad_model_id=args.cad_model_id,
    )
    if note:
        print(note)


def main() -> None:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_disp = sub.add_parser("dispatch")
    p_disp.add_argument("--message", required=True)
    p_disp.add_argument("--task-type", default="chat", choices=["chat", "spec", "code_fix"])
    p_disp.add_argument("--model-id", default=None)

    p_base = sub.add_parser("baseline")
    p_base.add_argument("--model-id", default=None)
    p_base.add_argument("--size", type=float, default=None)

    p_embed = sub.add_parser("wait-embed")
    p_embed.add_argument("--model-id", required=True)
    p_embed.add_argument("--spec-file", default=None)
    p_embed.add_argument("--spec-text", default="")
    p_embed.add_argument("--image-file", default=None)

    p_chat = sub.add_parser("wait-chat")
    p_chat.add_argument("--message", default="")
    p_chat.add_argument("--message-file", default=None)
    p_chat.add_argument("--image-file", default=None)

    p_cli = sub.add_parser("cli-exec")
    p_cli.add_argument("--model", default="claude-sonnet", help="Model alias from MODEL_POOL")
    p_cli.add_argument("--complexity", type=float, default=0.4)
    p_cli.add_argument("--task-pattern", default="general")
    p_cli.add_argument("--cad-model-id", default="")
    p_cli.add_argument("--prompt", default="")
    p_cli.add_argument("--prompt-file", default=None)
    p_cli.add_argument("--summary", default="Worker task execution")
    p_cli.add_argument("--cwd", default=None)

    p_telem = sub.add_parser("record-telemetry")
    p_telem.add_argument("--model", required=True)
    p_telem.add_argument("--task-pattern", default="general")
    p_telem.add_argument("--cad-model-id", default="")
    p_telem.add_argument("--elapsed", type=float, required=True)
    p_telem.add_argument("--failed", action="store_true")
    p_telem.add_argument("--timed-out", action="store_true")

    # Keep claude-exec alias for backwards compatibility
    p_claude = sub.add_parser("claude-exec")
    p_claude.add_argument("--model", default="claude-sonnet")
    p_claude.add_argument("--complexity", type=float, default=0.4)
    p_claude.add_argument("--task-pattern", default="general")
    p_claude.add_argument("--cad-model-id", default="")
    p_claude.add_argument("--prompt", default="")
    p_claude.add_argument("--prompt-file", default=None)
    p_claude.add_argument("--summary", default="Claude CLI execution")
    p_claude.add_argument("--cwd", default=None)

    args = parser.parse_args()
    if args.cmd == "dispatch":
        cmd_dispatch(args)
    elif args.cmd == "baseline":
        cmd_baseline(args)
    elif args.cmd == "wait-embed":
        cmd_wait_embed(args)
    elif args.cmd == "wait-chat":
        cmd_wait_chat(args)
    elif args.cmd in ("cli-exec", "claude-exec"):
        cmd_cli_exec(args)
    elif args.cmd == "record-telemetry":
        cmd_record_telemetry(args)


if __name__ == "__main__":
    main()
