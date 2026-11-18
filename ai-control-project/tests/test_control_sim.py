import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from control_sim import Config, safety_analytic, safety_monte_carlo  # noqa: E402


def test_analytic_matches_monte_carlo():
    cfg = Config(n_tasks=200, attack_rate=0.02, audit_budget=0.05, separation=1.5)
    assert abs(safety_analytic(cfg) - safety_monte_carlo(cfg, episodes=20000)) < 0.02


def test_more_budget_never_hurts():
    lo = safety_analytic(Config(audit_budget=0.01))
    hi = safety_analytic(Config(audit_budget=0.10))
    assert hi >= lo


def test_better_monitor_never_hurts():
    assert safety_analytic(Config(separation=3.0)) >= safety_analytic(Config(separation=1.0))
