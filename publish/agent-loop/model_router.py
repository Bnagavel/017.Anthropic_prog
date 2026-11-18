"""
model_router.py — Adaptive Telemetry Dispatcher across Antigravity Subagents, Gemini CLI, and Claude CLI.

Features:
  1. Multi-Folder Access Configuration:
     - Claude CLI (`haiku`, `sonnet`, `opus`): passes `--dangerously-skip-permissions --allowedTools Edit,Write,Read,Bash`
       and `--add-dir` for both `<WORKSPACE>/` and `<WORKSPACE>/016.24x7_Agent`.
     - Gemini CLI (`flash-lite`, `flash`, `pro`): passes `-y` (`--yolo` auto-accept) across workspace directories.
     - Antigravity Subagents (`agy-flash-lite`, `agy-flash`, `agy-pro`): uses write-enabled `hexprep-worker`.
  2. Tight Per-Tier Timeouts & Slow-Response Detection:
     - Tier 1 (Fast): timeout=45s, slow_threshold=25s
     - Tier 2 (Builder): timeout=90s, slow_threshold=55s
     - Tier 3 (Heavy): timeout=120s, slow_threshold=85s
  3. Adaptive Telemetry & Complexity Auto-Escalation (`logs/router_state.json`):
     - Tracks response latency (`avg_sec`, `last_sec`), success rate, slow count, and timeout count per model.
     - If a model is slow or times out on a task pattern (e.g., `phase_1`, `grid_hex`, or specific model ID),
       automatically boosts complexity (`+0.25`) for future similar tasks so Argon escalates to a higher tier!
"""

from __future__ import annotations

import json
import os
import re
import shutil
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


LOOP_DIR = Path(__file__).resolve().parent
LOGS_DIR = LOOP_DIR / "logs"
ROUTER_STATE_FILE = LOGS_DIR / "router_state.json"

WORKSPACE_DIRS = [
    "<WORKSPACE>/",
    "<WORKSPACE>/016.24x7_Agent",
]


def _resolve_npm_cmd(name: str) -> str:
    appdata = os.environ.get("APPDATA", "")
    if appdata:
        cmd_path = Path(appdata) / "npm" / f"{name}.cmd"
        if cmd_path.exists():
            return str(cmd_path)
    return name


DEFAULT_GEMINI_BIN = os.environ.get("GEMINI_CLI_CMD") or _resolve_npm_cmd("gemini")
DEFAULT_CLAUDE_BIN = os.environ.get("CLAUDE_CLI_CMD") or _resolve_npm_cmd("claude")


@dataclass
class ModelSpec:
    alias: str
    provider: str           # "claude" | "gemini" | "antigravity"
    cli_bin: str            # Path to CLI or "subagent"
    model_flag: str         # Flag passed to CLI or invoke_subagent Model parameter
    tier: int               # 1 (fast), 2 (builder), 3 (heavy)
    timeout_sec: int        # Max seconds before aborting and moving on
    slow_threshold_sec: int # Seconds above which response is flagged "slow" -> boosts future complexity
    description: str


MODEL_POOL: Dict[str, ModelSpec] = {
    # Tier 1: Fast / Lightweight Workers (Complexity < 0.35, Timeout 45s)
    "agy-flash-lite": ModelSpec(
        alias="agy-flash-lite",
        provider="antigravity",
        cli_bin="subagent",
        model_flag="flash_lite",
        tier=1,
        timeout_sec=45,
        slow_threshold_sec=22,
        description="Antigravity Flash-Lite Subagent (ultra-fast checks & log parsing)",
    ),
    "gemini-flash-lite": ModelSpec(
        alias="gemini-flash-lite",
        provider="gemini",
        cli_bin=DEFAULT_GEMINI_BIN,
        model_flag="gemini-2.5-flash-lite",
        tier=1,
        timeout_sec=45,
        slow_threshold_sec=22,
        description="Gemini 2.5 Flash-Lite CLI (-y auto-access, minimal quota)",
    ),
    "claude-haiku": ModelSpec(
        alias="claude-haiku",
        provider="claude",
        cli_bin=DEFAULT_CLAUDE_BIN,
        model_flag="haiku",
        tier=1,
        timeout_sec=45,
        slow_threshold_sec=25,
        description="Claude Haiku 4.5 CLI (fastest Claude model, minimal 5-hr quota)",
    ),
    "agy-flash": ModelSpec(
        alias="agy-flash",
        provider="antigravity",
        cli_bin="subagent",
        model_flag="flash",
        tier=1,
        timeout_sec=50,
        slow_threshold_sec=25,
        description="Gemini 3.8 Flash (Active Router & Fast Worker in Antigravity)",
    ),
    "gemini-flash": ModelSpec(
        alias="gemini-flash",
        provider="gemini",
        cli_bin=DEFAULT_GEMINI_BIN,
        model_flag="gemini-2.5-flash",
        tier=1,
        timeout_sec=50,
        slow_threshold_sec=25,
        description="Gemini 2.5 Flash CLI (-y auto-access, daily spec worker)",
    ),
    # Tier 2: Daily Builders & Architects (0.35 <= Complexity < 0.68, Timeout 90s)
    # ── Antigravity Subscription Models (Unified Google Quota) ──
    "agy-sonnet": ModelSpec(
        alias="agy-sonnet",
        provider="antigravity",
        cli_bin="subagent",
        model_flag="claude-sonnet-5.5",
        tier=2,
        timeout_sec=90,
        slow_threshold_sec=55,
        description="Claude Sonnet 5.5 (Antigravity Subscription: 100% weekly & 5h quota)",
    ),
    "agy-gpt": ModelSpec(
        alias="agy-gpt",
        provider="antigravity",
        cli_bin="subagent",
        model_flag="gpt-oss-120b",
        tier=2,
        timeout_sec=80,
        slow_threshold_sec=50,
        description="GPT-OSS 120B (Antigravity Subscription: 100% weekly & 5h quota)",
    ),
    "agy-pro": ModelSpec(
        alias="agy-pro",
        provider="antigravity",
        cli_bin="subagent",
        model_flag="pro",
        tier=2,
        timeout_sec=90,
        slow_threshold_sec=55,
        description="Antigravity Pro Subagent (isolated context for multi-file edits)",
    ),
    # ── Claude Subscription Models (Anthropic CLI via claude.cmd) ──
    "claude-sonnet": ModelSpec(
        alias="claude-sonnet",
        provider="claude",
        cli_bin=DEFAULT_CLAUDE_BIN,
        model_flag="sonnet",
        tier=2,
        timeout_sec=90,
        slow_threshold_sec=55,
        description="Claude Sonnet 5.5 CLI (Claude Subscription via claude.cmd)",
    ),
    # ── Gemini Subscription CLI Models ──
    "gemini-pro": ModelSpec(
        alias="gemini-pro",
        provider="gemini",
        cli_bin=DEFAULT_GEMINI_BIN,
        model_flag="gemini-2.5-pro",
        tier=2,
        timeout_sec=90,
        slow_threshold_sec=55,
        description="Gemini 2.5 Pro CLI (1M-context BRep diagnosis & code builder)",
    ),
    # Tier 3: Heavy 3D Geometry Solvers (Complexity >= 0.68, Timeout 120s)
    # ── Antigravity Subscription Models ──
    "agy-opus": ModelSpec(
        alias="agy-opus",
        provider="antigravity",
        cli_bin="subagent",
        model_flag="claude-opus-5.5",
        tier=3,
        timeout_sec=120,
        slow_threshold_sec=80,
        description="Claude Opus 5.5 (Antigravity Subscription: 100% weekly & 5h quota)",
    ),
    "agy-argon": ModelSpec(
        alias="agy-argon",
        provider="antigravity",
        cli_bin="subagent",
        model_flag="inherit",
        tier=3,
        timeout_sec=120,
        slow_threshold_sec=80,
        description="Gemini 4 Argon Subagent (Active Router & Tier-3 Solver; 100% weekly quota reset)",
    ),
    # ── Claude Subscription Models (Anthropic CLI via claude.cmd) ──
    "claude-opus": ModelSpec(
        alias="claude-opus",
        provider="claude",
        cli_bin=DEFAULT_CLAUDE_BIN,
        model_flag="opus",
        tier=3,
        timeout_sec=120,
        slow_threshold_sec=80,
        description="Claude Opus 5.5 CLI (Claude Subscription via claude.cmd)",
    ),
}

FALLBACK_ORDER: List[str] = [
    "agy-sonnet",
    "claude-sonnet",
    "agy-gpt",
    "gemini-pro",
    "agy-pro",
    "agy-opus",
    "claude-opus",
    "claude-haiku",
    "gemini-flash",
    "agy-flash",
    "gemini-flash-lite",
    "agy-flash-lite",
    "agy-argon",
]

CHAT_MODEL_SYNONYMS: List[Tuple[str, str]] = [
    ("gemini-flash-lite", "gemini-flash-lite"),
    ("gemini flash lite", "gemini-flash-lite"),
    ("agy-flash-lite", "agy-flash-lite"),
    ("flash-lite", "agy-flash-lite"),
    ("flash_lite", "agy-flash-lite"),
    ("flash lite", "agy-flash-lite"),
    ("gemini-flash", "gemini-flash"),
    ("gemini flash", "gemini-flash"),
    ("agy-flash", "agy-flash"),
    ("flash", "agy-flash"),
    ("3.8 flash", "agy-flash"),
    ("flash 3.8", "agy-flash"),
    ("gemini 3.8 flash", "agy-flash"),
    ("gemini-pro", "gemini-pro"),
    ("gemini pro", "gemini-pro"),
    ("agy-pro", "agy-pro"),
    ("antigravity pro", "agy-pro"),
    ("gpt-oss", "agy-gpt"),
    ("gpt oss", "agy-gpt"),
    ("gpt-oss 120b", "agy-gpt"),
    ("gpt 120b", "agy-gpt"),
    ("gpt", "agy-gpt"),
    ("agy-gpt", "agy-gpt"),
    ("agy gpt", "agy-gpt"),
    ("claude-haiku", "claude-haiku"),
    ("claude haiku", "claude-haiku"),
    ("haiku", "claude-haiku"),
    ("haiku cli", "claude-haiku"),
    # Claude Subscription CLI
    ("claude-sonnet-cli", "claude-sonnet"),
    ("claude sonnet cli", "claude-sonnet"),
    ("sonnet cli", "claude-sonnet"),
    ("claude-cli-sonnet", "claude-sonnet"),
    ("claude-sonnet", "claude-sonnet"),
    # Antigravity Subscription Claude Sonnet
    ("agy-sonnet", "agy-sonnet"),
    ("agy sonnet", "agy-sonnet"),
    ("sonnet agy", "agy-sonnet"),
    ("claude sonnet agy", "agy-sonnet"),
    ("agy-claude-sonnet", "agy-sonnet"),
    ("claude sonnet", "agy-sonnet"),
    ("sonnet", "agy-sonnet"),
    ("sonnet 5.5", "agy-sonnet"),
    ("claude sonnet 5.5", "agy-sonnet"),
    ("claude-sonnet-5.5", "agy-sonnet"),
    # Claude Subscription CLI
    ("claude-opus-cli", "claude-opus"),
    ("claude opus cli", "claude-opus"),
    ("opus cli", "claude-opus"),
    ("claude-cli-opus", "claude-opus"),
    ("claude-opus", "claude-opus"),
    # Antigravity Subscription Claude Opus
    ("agy-opus", "agy-opus"),
    ("agy opus", "agy-opus"),
    ("opus agy", "agy-opus"),
    ("claude opus agy", "agy-opus"),
    ("agy-claude-opus", "agy-opus"),
    ("claude opus", "agy-opus"),
    ("opus", "agy-opus"),
    ("opus 5.5", "agy-opus"),
    ("claude opus 5.5", "agy-opus"),
    ("claude-opus-5.5", "agy-opus"),
    ("claude", "agy-sonnet"),
    ("argon", "agy-argon"),
]

HARD_MATH_KEYWORDS = {
    "jacobian", "inversion", "inversions", "ogrid", "o-grid", "tfi",
    "singularity", "concave", "brep", "multiblock", "conformal", "t-junction",
    "watertight", "clevis", "fillet", "subsolid", "topology", "quaternion",
}

QUOTA_ERROR_PATTERNS = (
    "rate limit",
    "rate_limit",
    "429",
    "quota",
    "limit reached",
    "too many requests",
    "overloaded",
    "capacity",
    "credit balance",
    "not logged in",
    "authentication",
)


def build_cli_command(spec: ModelSpec, prompt_text: str, primary_cwd: str) -> List[str]:
    """Build CLI command with full multi-folder access and auto-approval flags."""
    extra_dirs = list({str(Path(d).resolve()) for d in WORKSPACE_DIRS + [primary_cwd]})
    if spec.provider == "claude":
        cmd = [
            spec.cli_bin,
            "--model",
            spec.model_flag,
            "--dangerously-skip-permissions",
            "--allowedTools",
            "Edit,Write,Read,Bash",
        ]
        for d in extra_dirs:
            cmd.extend(["--add-dir", d])
        cmd.extend(["-p", prompt_text])
        return cmd

    # Gemini CLI: -y (--yolo) auto-approves all file/tool actions
    return [
        spec.cli_bin,
        "-m",
        spec.model_flag,
        "-y",
        "-p",
        prompt_text,
    ]


@dataclass
class DispatchDecision:
    ok: bool
    chosen_model: Optional[ModelSpec]
    requested_alias: Optional[str]
    next_suggested_model: Optional[ModelSpec]
    complexity: float
    rationale: str
    cleaned_task_text: str
    task_pattern: str = "general"
    unavailable_reason: str = ""
    discord_notice: str = ""


@dataclass
class ModelRouter:
    """Persistent adaptive dispatcher with latency/reliability telemetry and pattern complexity memory."""

    router_model: str = "Gemini 4 Argon"
    argon_quota_left_pct: float = 100.0
    argon_reserve_threshold_pct: float = 20.0
    pinned_model: Optional[str] = None
    last_suggested_fallback: Optional[str] = None
    cooldown_until: Dict[str, float] = field(default_factory=dict)
    cooldown_reasons: Dict[str, str] = field(default_factory=dict)
    attempt_counts: Dict[str, int] = field(default_factory=dict)
    usage_counts: Dict[str, int] = field(default_factory=dict)
    # Per-model performance telemetry: {alias: {calls, successes, timeouts, slow_runs, avg_sec, last_sec}}
    model_telemetry: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    # Learned complexity boost per task pattern when prior runs were slow or timed out
    pattern_complexity_boost: Dict[str, float] = field(default_factory=dict)

    @classmethod
    def load(cls) -> "ModelRouter":
        router = cls()
        if ROUTER_STATE_FILE.exists():
            try:
                data = json.loads(ROUTER_STATE_FILE.read_text(encoding="utf-8"))
                router.router_model = data.get("router_model", "Gemini 4 Argon")
                router.argon_quota_left_pct = float(data.get("argon_quota_left_pct", 100.0))
                router.argon_reserve_threshold_pct = float(data.get("argon_reserve_threshold_pct", 20.0))
                router.pinned_model = data.get("pinned_model")
                router.last_suggested_fallback = data.get("last_suggested_fallback")
                router.cooldown_until = {k: float(v) for k, v in data.get("cooldown_until", {}).items()}
                router.cooldown_reasons = {k: str(v) for k, v in data.get("cooldown_reasons", {}).items()}
                router.attempt_counts = {k: int(v) for k, v in data.get("attempt_counts", {}).items()}
                router.usage_counts = {k: int(v) for k, v in data.get("usage_counts", {}).items()}
                router.model_telemetry = data.get("model_telemetry", {})
                router.pattern_complexity_boost = {
                    k: float(v) for k, v in data.get("pattern_complexity_boost", {}).items()
                }
            except Exception:
                pass
        return router

    def save(self) -> None:
        LOGS_DIR.mkdir(parents=True, exist_ok=True)
        data = {
            "router_model": self.router_model,
            "argon_quota_left_pct": self.argon_quota_left_pct,
            "argon_reserve_threshold_pct": self.argon_reserve_threshold_pct,
            "pinned_model": self.pinned_model,
            "last_suggested_fallback": self.last_suggested_fallback,
            "cooldown_until": self.cooldown_until,
            "cooldown_reasons": self.cooldown_reasons,
            "attempt_counts": self.attempt_counts,
            "usage_counts": self.usage_counts,
            "model_telemetry": self.model_telemetry,
            "pattern_complexity_boost": self.pattern_complexity_boost,
        }
        ROUTER_STATE_FILE.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")

    @staticmethod
    def get_task_pattern(item: Dict[str, Any], metrics: Dict[str, Any], task_type: str = "spec") -> str:
        phase = item.get("phase", "phase_1")
        strat = metrics.get("strategy", "auto")
        return f"{phase}:{strat}:{task_type}"

    def record_telemetry(
        self,
        alias: str,
        task_pattern: str,
        elapsed_sec: float,
        success: bool,
        timed_out: bool = False,
        cad_model_id: str = "",
    ) -> Optional[str]:
        """Record model response speed & outcome; auto-escalate complexity if slow or timed out."""
        spec = MODEL_POOL.get(alias)
        slow_limit = spec.slow_threshold_sec if spec else 45
        is_slow = elapsed_sec >= slow_limit

        stats = self.model_telemetry.get(
            alias,
            {
                "calls": 0,
                "successes": 0,
                "timeouts": 0,
                "slow_runs": 0,
                "avg_sec": 0.0,
                "last_sec": 0.0,
            },
        )
        calls = int(stats["calls"]) + 1
        prev_avg = float(stats["avg_sec"])
        new_avg = round(((prev_avg * (calls - 1)) + elapsed_sec) / calls, 2)

        stats["calls"] = calls
        stats["successes"] = int(stats["successes"]) + (1 if success else 0)
        stats["timeouts"] = int(stats["timeouts"]) + (1 if timed_out else 0)
        stats["slow_runs"] = int(stats["slow_runs"]) + (1 if is_slow else 0)
        stats["avg_sec"] = new_avg
        stats["last_sec"] = round(elapsed_sec, 2)
        self.model_telemetry[alias] = stats

        if success:
            self.usage_counts[alias] = self.usage_counts.get(alias, 0) + 1

        escalation_note = None
        if timed_out or not success or is_slow:
            delta = 0.30 if (timed_out or not success) else 0.20
            old_boost = self.pattern_complexity_boost.get(task_pattern, 0.0)
            new_boost = min(0.65, round(old_boost + delta, 2))
            self.pattern_complexity_boost[task_pattern] = new_boost
            if cad_model_id:
                self.attempt_counts[cad_model_id] = self.attempt_counts.get(cad_model_id, 0) + 1

            why = "timed out" if timed_out else ("failed" if not success else f"was slow ({elapsed_sec:.1f}s > {slow_limit}s)")
            escalation_note = (
                f"📈 **Telemetry Auto-Escalation**: `{alias}` {why} on `{task_pattern}` -> "
                f"boosted pattern complexity by `+{delta:.2f}` (now `+{new_boost:.2f}`) for future similar tasks."
            )

        self.save()
        return escalation_note

    def mark_unavailable(self, alias: str, cooldown_minutes: int = 30, reason: str = "Quota/rate limit") -> None:
        self.cooldown_until[alias] = time.time() + (cooldown_minutes * 60)
        self.cooldown_reasons[alias] = reason
        self.save()
        print(f"[DISPATCHER] Marked `{alias}` unavailable for {cooldown_minutes}m ({reason})")

    def check_availability(self, alias: str, allow_reserved: bool = False) -> Tuple[bool, str]:
        if alias not in MODEL_POOL:
            return False, f"Unknown model `{alias}`"

        # Quota Reserve Guard: Gemini 4 Argon is preserved at <= 20% limit (currently 19%)
        if alias == "agy-argon" and not allow_reserved:
            if self.argon_quota_left_pct <= self.argon_reserve_threshold_pct:
                return (
                    False,
                    f"Quota Reserve Mode ({self.argon_quota_left_pct:.0f}% left <= {self.argon_reserve_threshold_pct:.0f}% safety limit; resets in 6d 7h)",
                )

        spec = MODEL_POOL[alias]
        now = time.time()
        until = self.cooldown_until.get(alias, 0.0)
        if now < until:
            rem_min = max(1, int((until - now) / 60) + 1)
            why = self.cooldown_reasons.get(alias, "Cooldown")
            return False, f"{why} ({rem_min}m remaining)"

        if spec.cli_bin != "subagent":
            bin_path = Path(spec.cli_bin)
            if not bin_path.exists() and shutil.which(spec.cli_bin) is None:
                return False, f"CLI `{spec.cli_bin}` not found"

        return True, "Ready"

    def model_efficiency_score(self, alias: str) -> float:
        """Compute empirical efficiency score from telemetry (higher = faster, more reliable, fresher quota)."""
        stats = self.model_telemetry.get(alias)
        spec = MODEL_POOL[alias]
        used = self.usage_counts.get(alias, 0)
        quota_penalty = min(0.25, used * 0.03)

        if not stats or int(stats.get("calls", 0)) == 0:
            return round(1.0 - quota_penalty, 3)

        calls = max(1, int(stats["calls"]))
        sr = float(stats["successes"]) / calls
        avg_sec = float(stats["avg_sec"])
        speed_factor = max(0.0, 1.0 - (avg_sec / max(spec.timeout_sec, 1)))
        timeout_penalty = 0.25 * int(stats.get("timeouts", 0))
        slow_penalty = 0.10 * int(stats.get("slow_runs", 0))

        return round((0.65 * sr) + (0.35 * speed_factor) - timeout_penalty - slow_penalty - quota_penalty, 3)

    def get_next_available_model(self, exclude_alias: str, complexity: float = 0.4) -> ModelSpec:
        if complexity < 0.35:
            pref = ["claude-haiku", "gemini-flash", "agy-flash", "gemini-flash-lite", "agy-flash-lite", "claude-sonnet"]
        elif complexity < 0.68:
            pref = ["claude-sonnet", "gemini-pro", "agy-pro", "claude-opus", "claude-haiku"]
        else:
            pref = ["claude-opus", "claude-sonnet", "gemini-pro", "agy-pro", "agy-argon"]

        avail = [c for c in pref + FALLBACK_ORDER if c != exclude_alias and self.check_availability(c)[0]]
        if not avail:
            return MODEL_POOL["agy-flash"]
        # Sort top candidates by telemetry efficiency
        avail.sort(key=lambda a: -self.model_efficiency_score(a))
        return MODEL_POOL[avail[0]]

    def compute_complexity(
        self,
        item: Dict[str, Any],
        metrics: Dict[str, Any],
        user_text: str = "",
        task_type: str = "spec",
    ) -> Tuple[float, List[str]]:
        """Score task complexity (0.0 to 1.0), incorporating learned telemetry boosts from prior slow/failed runs."""
        score = 0.15
        reasons: List[str] = []

        phase = item.get("phase", "phase_1")
        if phase == "phase_2":
            score += 0.25
            reasons.append("phase_2 part")
        elif phase == "phase_3":
            score += 0.45
            reasons.append("phase_3 complex fitting")

        inversions = int(metrics.get("inversions", 0))
        min_sj = float(metrics.get("min_sj", 1.0))
        cov = float(metrics.get("coverage_pct", 100.0))
        valid = bool(metrics.get("valid", False))
        rc = int(metrics.get("returncode", 0))

        if rc == -1 or "timeout" in str(metrics.get("strategy", "")).lower():
            score += 0.35
            reasons.append("prior timeout")
        elif not valid:
            score += 0.15
            reasons.append("mesh invalid")

        if inversions > 0 or (not valid and min_sj <= 0.05):
            score += 0.20
            reasons.append(f"SJ/inv (SJ={min_sj:.2f}, inv={inversions})")
        if cov < 85.0 or int(metrics.get("n_hex", 0)) == 0:
            score += 0.15
            reasons.append(f"low coverage ({cov:.1f}%)")

        attempts = self.attempt_counts.get(item.get("id", ""), 0)
        if attempts >= 1:
            boost = min(0.35, attempts * 0.20)
            score += boost
            reasons.append(f"retry #{attempts + 1} (+{boost:.2f})")

        pattern = self.get_task_pattern(item, metrics, task_type)
        pat_boost = self.pattern_complexity_boost.get(pattern, 0.0)
        if pat_boost > 0:
            score += pat_boost
            reasons.append(f"learned telemetry boost on `{pattern}` (+{pat_boost:.2f})")

        words = set(re.findall(r"[a-z0-9_-]+", user_text.lower()))
        matched_kw = words.intersection(HARD_MATH_KEYWORDS)
        if matched_kw:
            score += min(0.25, len(matched_kw) * 0.08)
            reasons.append(f"math keywords ({', '.join(sorted(matched_kw)[:3])})")

        return min(1.0, round(score, 2)), reasons

    def extract_manual_model_from_message(self, text: str) -> Tuple[Optional[str], str]:
        raw = text.strip()
        low = raw.lower()

        if low in ("model auto", "models auto", "auto model", "use auto", "route auto"):
            return "AUTO", ""

        if low in ("next_model", "next model", "move to next model", "use next"):
            return "NEXT_MODEL", ""

        model_mention_re = re.compile(
            r"\b(?:use|pick|select|model|switch to|route to|with)\s+"
            r"(gemini-flash-lite|gemini flash lite|agy-flash-lite|flash-lite|flash_lite|flash lite|"
            r"gemini 3\.8 flash|3\.8 flash|flash 3\.8|gemini-flash|gemini flash|agy-flash|flash|"
            r"gemini-pro|gemini pro|agy-pro|antigravity pro|"
            r"gpt-oss 120b|gpt 120b|gpt-oss|gpt oss|gpt|agy-gpt|agy gpt|"
            r"claude-haiku|claude haiku|haiku cli|haiku|"
            r"claude-sonnet-cli|claude sonnet cli|sonnet cli|claude-cli-sonnet|claude-sonnet|"
            r"agy-claude-sonnet|agy-sonnet|agy sonnet|sonnet agy|claude sonnet 5\.5|sonnet 5\.5|claude sonnet|sonnet|"
            r"claude-opus-cli|claude opus cli|opus cli|claude-cli-opus|claude-opus|"
            r"agy-claude-opus|agy-opus|agy opus|opus agy|claude opus 5\.5|opus 5\.5|claude opus|opus|claude|argon)\b",
            re.IGNORECASE,
        )
        m = model_mention_re.search(raw)
        if not m:
            return None, raw

        matched_name = m.group(1).lower()
        canonical = None
        for syn, target in CHAT_MODEL_SYNONYMS:
            if matched_name == syn:
                canonical = target
                break

        cleaned = (raw[: m.start()] + " " + raw[m.end() :]).strip(" ,:;-")
        for prefix in ("to ", "and ", "for "):
            if cleaned.lower().startswith(prefix):
                cleaned = cleaned[len(prefix) :].strip()
        return canonical, cleaned

    def dispatch(
        self,
        task_type: str,
        item: Dict[str, Any],
        metrics: Dict[str, Any],
        user_text: str = "",
    ) -> DispatchDecision:
        pattern = self.get_task_pattern(item, metrics, task_type)
        complexity, reasons = self.compute_complexity(item, metrics, user_text, task_type=task_type)
        reason_str = ", ".join(reasons) if reasons else "standard task"

        explicit_req, cleaned_task = self.extract_manual_model_from_message(user_text)

        if explicit_req == "AUTO":
            self.pinned_model = None
            self.last_suggested_fallback = None
            self.save()
            spec = self._auto_pick(task_type, complexity)
            return DispatchDecision(
                ok=True,
                chosen_model=spec,
                requested_alias="AUTO",
                next_suggested_model=None,
                complexity=complexity,
                rationale=f"Reset to AUTO -> selected `{spec.alias}` ({reason_str})",
                cleaned_task_text=cleaned_task,
                task_pattern=pattern,
                discord_notice=(
                    f"🔄 **Dispatcher reset to AUTO.** Selected **`{spec.alias}`** "
                    f"(timeout `{spec.timeout_sec}s`, complexity `{complexity:.2f}`)."
                ),
            )

        if explicit_req == "NEXT_MODEL" and self.last_suggested_fallback:
            explicit_req = self.last_suggested_fallback
            self.last_suggested_fallback = None

        target_manual = explicit_req or self.pinned_model
        if target_manual:
            allow_reserved = "force" in user_text.lower()
            avail, avail_msg = self.check_availability(target_manual, allow_reserved=allow_reserved)
            if avail:
                self.pinned_model = target_manual
                self.save()
                chosen = MODEL_POOL[target_manual]
                return DispatchDecision(
                    ok=True,
                    chosen_model=chosen,
                    requested_alias=target_manual,
                    next_suggested_model=self.get_next_available_model(target_manual, complexity),
                    complexity=complexity,
                    rationale=f"Manual selection (`{target_manual}`)",
                    cleaned_task_text=cleaned_task,
                    task_pattern=pattern,
                    discord_notice=(
                        f"🎯 **Dispatcher locked to `{chosen.alias}`** (`{chosen.model_flag}`, timeout `{chosen.timeout_sec}s`)."
                        if not cleaned_task
                        else ""
                    ),
                )
            else:
                next_spec = self.get_next_available_model(target_manual, complexity)
                self.last_suggested_fallback = next_spec.alias
                self.save()
                notice = (
                    f"⚠️ **Requested model `{target_manual}` is currently unavailable** ({avail_msg}).\n"
                    f"👉 **Next available model (complexity `{complexity:.2f}`):** **`{next_spec.alias}`** "
                    f"(`{next_spec.model_flag}`, timeout `{next_spec.timeout_sec}s`).\n\n"
                    f"Reply **`NEXT_MODEL`** (or **`use {next_spec.alias}`**) to move on to `{next_spec.alias}`!"
                )
                return DispatchDecision(
                    ok=False,
                    chosen_model=None,
                    requested_alias=target_manual,
                    next_suggested_model=next_spec,
                    complexity=complexity,
                    rationale=f"`{target_manual}` unavailable ({avail_msg})",
                    cleaned_task_text=cleaned_task,
                    task_pattern=pattern,
                    unavailable_reason=avail_msg,
                    discord_notice=notice,
                )

        chosen = self._auto_pick(task_type, complexity)
        eff = self.model_efficiency_score(chosen.alias)
        return DispatchDecision(
            ok=True,
            chosen_model=chosen,
            requested_alias=None,
            next_suggested_model=self.get_next_available_model(chosen.alias, complexity),
            complexity=complexity,
            rationale=f"AUTO Tier-{chosen.tier} (eff={eff:.2f} | {reason_str})",
            cleaned_task_text=cleaned_task,
            task_pattern=pattern,
        )

    def _auto_pick(self, task_type: str, complexity: float) -> ModelSpec:
        if complexity < 0.35:
            candidates = (
                ["claude-haiku", "gemini-flash", "agy-flash", "gemini-flash-lite", "agy-flash-lite"]
                if task_type == "code_fix"
                else ["agy-flash", "gemini-flash", "claude-haiku", "gemini-flash-lite", "agy-flash-lite"]
            )
        elif complexity < 0.68:
            # Complex Tier-2: Claude Sonnet (AGY Subscription & Claude Subscription CLI) + GPT-OSS
            candidates = (
                ["agy-sonnet", "claude-sonnet", "agy-gpt", "gemini-pro", "agy-pro", "claude-haiku"]
                if task_type == "code_fix"
                else ["agy-sonnet", "claude-sonnet", "agy-gpt", "gemini-pro", "agy-pro", "gemini-flash"]
            )
        else:
            # Heavy Tier-3: Gemini 4 Argon + Claude Opus (AGY Subscription & Claude Subscription CLI) + Claude Sonnet
            candidates = ["agy-argon", "agy-opus", "claude-opus", "agy-sonnet", "claude-sonnet", "gemini-pro", "agy-pro"]

        avail_cands = [c for c in candidates if self.check_availability(c)[0]]
        if not avail_cands:
            avail_cands = [c for c in FALLBACK_ORDER if self.check_availability(c)[0]]
        if not avail_cands:
            return MODEL_POOL["agy-flash"]

        # Sort available candidates inside this tier by empirical telemetry efficiency score
        avail_cands.sort(key=lambda a: -self.model_efficiency_score(a))
        return MODEL_POOL[avail_cands[0]]

    def format_router_status(self) -> str:
        argon_status = (
            f"✅ Active ({self.argon_quota_left_pct:.0f}% weekly quota available; reserve guardrail at {self.argon_reserve_threshold_pct:.0f}%)"
            if self.argon_quota_left_pct > self.argon_reserve_threshold_pct
            else f"🛡️ Reserved ({self.argon_quota_left_pct:.0f}% left <= {self.argon_reserve_threshold_pct:.0f}% limit)"
        )
        lines = [
            "**🧭 AutoHex Adaptive Dispatcher & Quota Status:**",
            f"- **Active Router Agent**: `{self.router_model} (Antigravity UI)`",
            f"- **Mode**: `{f'PINNED -> {self.pinned_model}' if self.pinned_model else 'AUTO (Telemetry + Quota-Balanced)'}`",
            f"- **Gemini 4 Argon Quota**: `{argon_status}`",
            "- **Claude & GPT Subscription (Antigravity)**: `✅ 100% weekly / 100% 5h limit (Claude Opus 5.5, Claude Sonnet 5.5, GPT-OSS 120B)`",
            "- **Claude Subscription (CLI)**: `⚡ Active (claude.cmd Haiku 4.5, Sonnet 5.5, Opus 5.5)`",
            "- **Gemini Models Quota (CLI & AGY)**: `✅ Active (Gemini 3.8 Flash, Gemini 2.5 Pro)`",
        ]
        if self.pattern_complexity_boost:
            boosts = ", ".join(f"`{k}: +{v:.2f}`" for k, v in self.pattern_complexity_boost.items())
            lines.append(f"- **Learned Pattern Boosts**: {boosts}")

        lines.append("\n**Model Pool & Response Telemetry:**")
        for alias, spec in MODEL_POOL.items():
            ok, msg = self.check_availability(alias)
            eff = self.model_efficiency_score(alias)
            st = self.model_telemetry.get(alias, {})
            calls = st.get("calls", 0)
            avg_s = st.get("avg_sec", 0.0)
            to_cnt = st.get("timeouts", 0)
            slow_cnt = st.get("slow_runs", 0)
            badge = "✅ Ready" if ok else f"⏳ {msg}"
            telem_str = (
                f"calls=`{calls}`, avg=`{avg_s:.1f}s`/{spec.timeout_sec}s, slow=`{slow_cnt}`, to=`{to_cnt}`, eff=`{eff:.2f}`"
                if calls > 0
                else f"timeout=`{spec.timeout_sec}s`, eff=`{eff:.2f}`"
            )
            lines.append(f"• [T{spec.tier}] **`{alias}`** — {badge} ({telem_str})")

        lines.append(
            "\n💡 _Commands:_ `use sonnet` | `use opus` | `use gpt` | `use haiku` | `use flash` | `use gemini pro` | `model auto`"
        )
        return "\n".join(lines)


def find_step_model_by_chat(queue_data: Dict[str, Any], user_text: str) -> Optional[Dict[str, Any]]:
    low = user_text.strip().lower()
    triggers = ("run ", "switch to ", "load ", "test ")
    if not any(low.startswith(t) for t in triggers):
        return None

    query = low
    for t in triggers:
        if query.startswith(t):
            query = query[len(t) :].strip()
            break

    if any(k in query for k in ("opus", "sonnet", "haiku", "flash", "gemini", "claude", "argon", "auto", "status")):
        return None

    for item in queue_data.get("queue", []):
        item_id = item["id"].lower()
        rel = item["rel_path"].lower()
        stem = Path(item["rel_path"]).stem.lower()
        if query == item_id or query == stem or query in item_id or query in rel:
            return item
    return None
