"""
daily_orchestrator.py — Continuous & Single-Run AutoHex Loop with Discord Chat
and Dynamic Gemini/Claude Model Routing.

Modes:
  1. Continuous Chat Mode (default):
     Keeps Discord chat active all the time so you can converse with Gemini/Claude,
     dynamically switch CAD models or AI models, adjust mesh size, and trigger fixes
     directly from your phone.
  2. Dry-Run Test:
     python daily_orchestrator.py --dry-run
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

from discord_gate import (
    load_env_file,
    send_status_embed,
    send_text_message,
    wait_for_next_user_message,
)
from model_router import ModelRouter, find_step_model_by_chat


LOOP_DIR = Path(__file__).resolve().parent
QUEUE_FILE = LOOP_DIR / "queue.json"
LOGS_DIR = LOOP_DIR / "logs"


def load_queue() -> Dict[str, Any]:
    return json.loads(QUEUE_FILE.read_text(encoding="utf-8"))


def save_queue(data: Dict[str, Any]) -> None:
    QUEUE_FILE.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def select_next_item(data: Dict[str, Any], model_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
    for item in data.get("queue", []):
        if model_id and item["id"] == model_id:
            return item
        if not model_id and item.get("status") in ("in_progress", "pending"):
            return item
    return None


def format_queue_summary(data: Dict[str, Any], active_id: str = "") -> str:
    lines = ["**📋 AutoHex Test Queue Status:**"]
    for idx, item in enumerate(data.get("queue", []), 1):
        marker = "👉 " if item["id"] == active_id else ""
        st = item.get("status", "pending").upper()
        m = item.get("metrics", {})
        extra = ""
        if m:
            extra = f" — `hex={m.get('n_hex', 0)}, cov={m.get('coverage_pct', 0):.1f}%, minSJ={m.get('min_sj', 0):.2f}`"
        lines.append(f"{marker}`{idx:02d}.` **{item['id']}** (`{item['rel_path']}`) : `{st}`{extra}")
    lines.append("\n💡 _Jump to any CAD model by typing:_ `run <model_id or name>` (e.g., `run lug_with_fillets`)")
    return "\n".join(lines)


def run_hexprep_baseline(
    project_root: Path,
    step_path: Path,
    target_size_mm: float,
    output_msh: Path,
) -> Dict[str, Any]:
    """Run hexprep CLI on a STEP model and parse output metrics."""
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    output_msh.parent.mkdir(parents=True, exist_ok=True)

    venv_python = project_root / ".venv" / "Scripts" / "python.exe"
    default_python = str(venv_python) if venv_python.exists() else sys.executable
    python_exe = os.environ.get("AUTOHEX_PYTHON") or default_python

    cmd = [
        python_exe,
        "-c",
        "import sys; from hexprep.cli import main; main()",
        "mesh",
        str(step_path),
        "-o",
        str(output_msh),
        "--size",
        str(target_size_mm),
        "--quality",
        "--verbose",
    ]

    env = os.environ.copy()
    src_dir = str(project_root / "src")
    env["PYTHONPATH"] = f"{src_dir}{os.pathsep}{env.get('PYTHONPATH', '')}"
    env["PYTHONIOENCODING"] = "utf-8"

    print(f"[RUN] Running HexPrep on {step_path.name} (size={target_size_mm}mm)...")
    try:
        proc = subprocess.run(
            cmd,
            cwd=str(project_root),
            env=env,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=90,
        )
        combined_log = (proc.stdout or "") + "\n" + (proc.stderr or "")
        rc = proc.returncode
    except subprocess.TimeoutExpired as exc:
        out_str = exc.stdout.decode("utf-8", errors="replace") if isinstance(exc.stdout, bytes) else (exc.stdout or "")
        err_str = exc.stderr.decode("utf-8", errors="replace") if isinstance(exc.stderr, bytes) else (exc.stderr or "")
        combined_log = out_str + "\n" + err_str + f"\n[TIMEOUT] HexPrep timed out after {exc.timeout}s"
        rc = -1

    metrics = parse_hexprep_log(combined_log, returncode=rc)
    metrics["raw_log"] = combined_log
    return metrics


def parse_hexprep_log(log_text: str, returncode: int) -> Dict[str, Any]:
    """Extract key metrics (winner, n_hex, coverage, minSJ, maxAR, inversions) from CLI output."""
    valid = (
        returncode == 0
        and "No valid mesh produced" not in log_text
        and bool(log_text.strip())
    )
    strategy = "none"
    n_hex = 0
    coverage_pct = 0.0
    min_sj = 0.0
    max_ar = 0.0
    inversions = 0

    winner_match = re.search(r"Winner\s*:\s*(\w+)", log_text, re.IGNORECASE)
    if winner_match:
        strategy = winner_match.group(1)

    for m in re.finditer(r"(\d+)\s+hex", log_text, re.IGNORECASE):
        n_hex = int(m.group(1))

    for m in re.finditer(r"coverage[=:\s]+([0-9.]+)%", log_text, re.IGNORECASE):
        coverage_pct = float(m.group(1))

    for m in re.finditer(r"min[_\s]*SJ[=:\s]+(-?[0-9.]+)", log_text, re.IGNORECASE):
        min_sj = float(m.group(1))

    for m in re.finditer(r"max[_\s]*AR[=:\s]+([0-9.]+)", log_text, re.IGNORECASE):
        max_ar = float(m.group(1))

    for m in re.finditer(r"inv(?:ersions)?[=:\s]+(\d+)", log_text, re.IGNORECASE):
        inversions = int(m.group(1))

    valid = (
        returncode == 0
        and "No valid mesh produced" not in log_text
        and bool(log_text.strip())
        and strategy not in ("none", "grid_hex")
        and 94.0 <= coverage_pct <= 106.0
        and min_sj > 0.05
        and inversions == 0
    )

    return {
        "valid": valid,
        "returncode": returncode,
        "strategy": strategy,
        "n_hex": n_hex,
        "coverage_pct": coverage_pct,
        "min_sj": min_sj,
        "max_ar": max_ar,
        "inversions": inversions,
    }


def generate_routed_spec(
    router: ModelRouter,
    project_root: Path,
    item: Dict[str, Any],
    metrics: Dict[str, Any],
    user_feedback: str = "",
    chat_history: Optional[List[str]] = None,
) -> str:
    """Use ModelRouter to pick the right Gemini/Claude model and generate a concise diagnosis/spec."""
    model_id = item["id"]
    rel_path = item["rel_path"]
    log_tail = "\n".join(metrics.get("raw_log", "").splitlines()[-80:])
    history_block = "\n".join(chat_history[-6:]) if chat_history else ""
    feedback_block = f"\nLatest User Message / Refinement: {user_feedback}\n" if user_feedback else ""

    prompt = (
        f"You are diagnosing HexPrep (<WORKSPACE>/) for model `{rel_path}`.\n"
        f"Baseline result: valid={metrics['valid']}, strategy={metrics['strategy']}, "
        f"n_hex={metrics['n_hex']}, coverage={metrics['coverage_pct']}%, "
        f"minSJ={metrics['min_sj']}, maxAR={metrics['max_ar']}, inversions={metrics['inversions']}.\n"
        f"{history_block}\n{feedback_block}\n"
        f"Recent log tail:\n```\n{log_tail}\n```\n\n"
        "Inspect the relevant modules in `src/hexprep/` (`sweep_detector.py`, `sweep_mesher.py`, "
        "`brep_graph.py`, `multiblock_mesher.py`, `mesh_validator.py`) and respond concisely "
        "(under 250 words) for Discord mobile:\n"
        "- Direct answer to any user question/refinement\n"
        "- Root Cause & exact files/functions to modify\n"
        "- Verification criteria"
    )

    spec_file = LOGS_DIR / f"{model_id}_gemini_spec.md"
    task_type = "chat" if user_feedback else "spec"

    ok, out_text, chosen_spec, complexity, rationale = router.run_With_fallback(
        task_type=task_type,
        prompt=prompt,
        cwd=project_root,
        item=item,
        metrics=metrics,
        user_text=user_feedback,
        timeout_sec=180,
    )
    next_coder, _, _ = router.select_model("code_fix", item, metrics, user_feedback)
    route_header = (
        f"🧭 **Router:** `{chosen_spec.alias}` (complexity `{complexity:.2f}`: _{rationale}_) "
        f"→ **Coder:** `{next_coder.alias}`\n"
    )

    if ok and out_text:
        full_text = route_header + "\n" + out_text
        spec_file.write_text(full_text, encoding="utf-8")
        return full_text

    fallback_spec = (
        route_header
        + f"### Automated Diagnosis Summary (`{model_id}`)\n"
        f"- **Valid**: `{metrics['valid']}` (Return code `{metrics['returncode']}`)\n"
        f"- **Metrics**: `n_hex={metrics['n_hex']}`, `coverage={metrics['coverage_pct']}%`, "
        f"`minSJ={metrics['min_sj']}`, `inversions={metrics['inversions']}`\n"
        f"{feedback_block}\n"
        f"**Log Tail:**\n```text\n{log_tail[-800:]}\n```"
    )
    spec_file.write_text(fallback_spec, encoding="utf-8")
    return fallback_spec


def execute_routed_fix(
    router: ModelRouter,
    project_root: Path,
    item: Dict[str, Any],
    metrics: Dict[str, Any],
    approved_spec: str,
) -> tuple[bool, str]:
    """Create/switch to branch `fix/<model_id>` and use ModelRouter to execute the fix with failover."""
    model_id = item["id"]
    rel_path = item["rel_path"]
    router.record_attempt(model_id)

    branch_name = f"fix/{model_id}"
    subprocess.run(
        ["git", "checkout", "-B", branch_name],
        cwd=str(project_root),
        capture_output=True,
        text=True,
    )

    prompt = (
        f"Implement the following approved HexPrep fix spec for `{rel_path}`.\n\n"
        f"{approved_spec}\n\n"
        "Keep changes minimal and focused in `src/hexprep/`, then run validation."
    )

    ok, out_text, chosen_spec, complexity, rationale = router.run_With_fallback(
        task_type="code_fix",
        prompt=prompt,
        cwd=project_root,
        item=item,
        metrics=metrics,
        user_text=approved_spec,
        timeout_sec=600,
    )
    (LOGS_DIR / f"{model_id}_code_exec.log").write_text(out_text or "", encoding="utf-8")
    summary = f"Executed via `{chosen_spec.alias}` (complexity `{complexity:.2f}`, {rationale})"
    return ok, summary


def run_continuous_chat_loop(args: argparse.Namespace) -> None:
    """Keep Discord chat active continuously with dynamic CAD & AI model switching."""
    queue_data = load_queue()
    project_root = Path(queue_data["project_root"])
    models_root = Path(queue_data["models_root"])
    router = ModelRouter()

    current_item = select_next_item(queue_data, model_id=args.model_id)
    if not current_item:
        send_text_message("🎉 All models in `queue.json` are marked `passed`! Reply `STATUS` or `run <name>` to re-run any model.")
        return

    chat_history: List[str] = []

    def _run_and_post(item: Dict[str, Any], user_note: str = "") -> tuple[Dict[str, Any], str, Optional[str]]:
        model_id = item["id"]
        rel_path = item["rel_path"]
        step_path = models_root / rel_path
        target_size = float(item.get("target_size_mm", queue_data.get("default_target_size_mm", 1.5)))
        output_msh = LOGS_DIR / f"{model_id}.msh"

        item["status"] = "in_progress"
        item["last_run"] = dt.datetime.now(dt.timezone.utc).isoformat()
        if not args.dry_run:
            save_queue(queue_data)

        if args.dry_run:
            metrics = {
                "valid": False,
                "returncode": 1,
                "strategy": "multiblock",
                "n_hex": 310,
                "coverage_pct": 88.4,
                "min_sj": 0.08,
                "max_ar": 12.4,
                "inversions": 2,
                "raw_log": "Dry-run test log: Strategy A skipped; Strategy B minSJ=0.08, inv=2.",
            }
        else:
            metrics = run_hexprep_baseline(project_root, step_path, target_size, output_msh)
            (LOGS_DIR / f"{model_id}_baseline.log").write_text(metrics.get("raw_log", ""), encoding="utf-8")

        item["metrics"] = {k: v for k, v in metrics.items() if k != "raw_log"}
        if not args.dry_run:
            save_queue(queue_data)

        spec = generate_routed_spec(
            router, project_root, item, metrics, user_feedback=user_note, chat_history=chat_history
        )
        status_label = "VALID (Quality Check)" if metrics["valid"] else "NEEDS FIX"
        msg_id = send_status_embed(
            title=f"AutoHex Continuous Chat: {model_id}",
            model_rel_path=f"{rel_path} (size={target_size}mm)",
            status=status_label,
            metrics=metrics,
            gemini_spec_summary=spec
            + "\n\n💬 **Commands:** `PROCEED` | `NEXT` | `SKIP` | `SIZE 1.0` | `STATUS` | `MODELS` | `STOP`\n"
            "🔀 **Switch CAD or AI Model:** `run <step_name>` | `use opus` | `use sonnet` | `use flash` | `model auto`",
            color=0x2ECC71 if metrics["valid"] else 0xE67E22,
        )
        return metrics, spec, msg_id

    metrics, current_spec, last_msg_id = _run_and_post(current_item)

    while True:
        user_msg, last_msg_id = wait_for_next_user_message(after_message_id=last_msg_id)
        cmd_upper = user_msg.strip().upper()
        print(f"[DISCORD USER] {user_msg}")

        if cmd_upper in ("STOP", "EXIT", "QUIT"):
            send_text_message("👋 Stopping AutoHex continuous Discord listener.")
            break

        if cmd_upper in ("STATUS", "QUEUE"):
            last_msg_id = send_text_message(format_queue_summary(queue_data, active_id=current_item["id"]))
            continue

        # 1. Check if user is querying or overriding the AI Model Router
        router_reply = router.parse_chat_model_override(user_msg)
        if router_reply:
            last_msg_id = send_text_message(router_reply)
            continue

        # 2. Check if user is switching the active CAD .step model dynamically
        switched_item = find_step_model_by_chat(queue_data, user_msg)
        if switched_item:
            current_item = switched_item
            chat_history.clear()
            send_text_message(f"📂 Switching active CAD model to **`{current_item['id']}`** (`{current_item['rel_path']}`)...")
            metrics, current_spec, last_msg_id = _run_and_post(current_item)
            continue

        if cmd_upper.startswith("SIZE "):
            try:
                new_size = float(user_msg.strip().split()[1])
                current_item["target_size_mm"] = new_size
                send_text_message(f"🔄 Re-running `{current_item['id']}` with `--size {new_size}` mm...")
                metrics, current_spec, last_msg_id = _run_and_post(current_item)
            except ValueError:
                last_msg_id = send_text_message("⚠️ Usage: `SIZE 1.0`")
            continue

        if cmd_upper == "SKIP":
            current_item["status"] = "skipped"
            if not args.dry_run:
                save_queue(queue_data)
            next_item = select_next_item(queue_data)
            if not next_item:
                last_msg_id = send_text_message("🎉 End of queue reached! Reply `STATUS`, `run <name>`, or `STOP`.")
                continue
            current_item = next_item
            chat_history.clear()
            metrics, current_spec, last_msg_id = _run_and_post(current_item)
            continue

        if cmd_upper == "NEXT":
            if metrics.get("valid"):
                current_item["status"] = "passed"
                if not args.dry_run:
                    save_queue(queue_data)
            next_item = None
            for it in queue_data.get("queue", []):
                if it["id"] != current_item["id"] and it.get("status") in ("pending", "in_progress"):
                    next_item = it
                    break
            if not next_item:
                last_msg_id = send_text_message("🎉 No more pending models in `queue.json`! Reply `STATUS`, `run <name>`, or `STOP`.")
                continue
            current_item = next_item
            chat_history.clear()
            metrics, current_spec, last_msg_id = _run_and_post(current_item)
            continue

        if cmd_upper in ("PROCEED", "FIX"):
            model_id = current_item["id"]
            rel_path = current_item["rel_path"]
            step_path = models_root / rel_path
            target_size = float(current_item.get("target_size_mm", 1.5))
            output_msh = LOGS_DIR / f"{model_id}.msh"

            chosen_coder, c_score, c_reason = router.select_model("code_fix", current_item, metrics, current_spec)
            send_text_message(
                f"⚙️ Executing code fix on branch `fix/{model_id}` via **`{chosen_coder.alias}`** "
                f"(complexity `{c_score:.2f}`: _{c_reason}_)..."
            )
            exec_summary = "Dry-run mode (no code modified)"
            if not args.dry_run:
                _, exec_summary = execute_routed_fix(router, project_root, current_item, metrics, current_spec)
                metrics = run_hexprep_baseline(project_root, step_path, target_size, output_msh)
                current_item["metrics"] = {k: v for k, v in metrics.items() if k != "raw_log"}
                current_item["status"] = "passed" if metrics["valid"] else "in_progress"
                save_queue(queue_data)

            last_msg_id = send_status_embed(
                title=f"AutoHex Post-Fix Result: {model_id}",
                model_rel_path=rel_path,
                status="PASSED" if metrics["valid"] else "STILL FAILING",
                metrics=metrics,
                gemini_spec_summary=(
                    f"{exec_summary}\n"
                    f"Branch `fix/{model_id}` updated and validated.\n"
                    "Reply `NEXT` for next model, `PROCEED` to retry (auto-escalates complexity), or type instructions!"
                ),
                color=0x2ECC71 if metrics["valid"] else 0xE74C3C,
            )
            continue

        # Free-form chat -> converse with routed model!
        clean_note = user_msg.split(":", 1)[1].strip() if cmd_upper.startswith("REFINE:") else user_msg
        chat_history.append(f"User: {clean_note}")
        current_spec = generate_routed_spec(
            router,
            project_root,
            current_item,
            metrics,
            user_feedback=clean_note,
            chat_history=chat_history,
        )
        chat_history.append(f"Assistant: {current_spec[:400]}")
        last_msg_id = send_text_message(
            f"🤖 **Updated Spec / Reply (`{current_item['id']}`):**\n{current_spec}\n\n"
            "_Reply `PROCEED` to execute this fix, `NEXT` for next model, or keep chatting!_"
        )


def main() -> None:
    parser = argparse.ArgumentParser(description="Daily AutoHex Gemini/Claude Routed Discord Loop")
    parser.add_argument("--model-id", help="Run a specific model ID from queue.json")
    parser.add_argument("--dry-run", action="store_true", help="Skip HexPrep execution and test Discord gate")
    args = parser.parse_args()

    load_env_file()
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    run_continuous_chat_loop(args)


if __name__ == "__main__":
    main()
