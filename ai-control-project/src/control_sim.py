"""Toy simulation of *trusted monitoring with a limited audit budget*.

Setting (simplified from Greenblatt et al., 2023, "AI Control: Improving Safety
Despite Intentional Subversion"):

* An untrusted model completes N tasks. Each task it may *attack* (insert a
  backdoor) with probability `attack_rate`.
* A trusted monitor gives every output a suspicion score. Benign ~ N(0, 1),
  attacks ~ N(separation, 1). Higher separation = better monitor.
* Humans can audit only a fraction `audit_budget` of tasks; we audit the
  highest-scoring ones, i.e. the threshold is set so that a benign output is
  audited with probability == audit_budget.
* Blue team wins if an attack is audited (model caught -> shutdown).
  Red team wins if an attack gets through unaudited and succeeds.

`safety` = P(blue wins before red does). This is the quantity the red team
tries to minimise by choosing `attack_rate`, and the blue team tries to
maximise by choosing the audit policy.

Analogy to damage tolerance: audit budget ~ inspection effort, monitor
separation ~ probability of detection, attack_rate ~ flaw initiation rate.
"""

from __future__ import annotations

import random
from dataclasses import dataclass
from statistics import NormalDist

_ND = NormalDist()


@dataclass(frozen=True)
class Config:
    n_tasks: int = 1000
    attack_rate: float = 0.01
    audit_budget: float = 0.02
    separation: float = 2.0
    attack_success: float = 0.5  # P(unaudited attack actually succeeds)


def threshold(audit_budget: float) -> float:
    """Score above which an output is audited (benign false-positive rate = budget)."""
    return _ND.inv_cdf(1.0 - audit_budget)


def p_caught(cfg: Config) -> float:
    """P(an individual attack is audited)."""
    t = threshold(cfg.audit_budget)
    return 1.0 - _ND.cdf(t - cfg.separation)


def safety_analytic(cfg: Config) -> float:
    """Closed form: per attack, caught w.p. c, else succeeds w.p. s.
    Safety = P(first decisive event is a catch, or no decisive event)."""
    c = p_caught(cfg)
    s = (1.0 - c) * cfg.attack_success
    decisive = c + s
    p_no_attack_decisive = (1.0 - cfg.attack_rate * decisive) ** cfg.n_tasks
    if decisive == 0:
        return 1.0
    p_any = 1.0 - p_no_attack_decisive
    return p_no_attack_decisive + p_any * (c / decisive)


def safety_monte_carlo(cfg: Config, episodes: int = 20000, seed: int = 0) -> float:
    rng = random.Random(seed)
    t = threshold(cfg.audit_budget)
    blue = 0
    for _ in range(episodes):
        outcome = "blue"  # no successful attack => safe
        for _ in range(cfg.n_tasks):
            if rng.random() >= cfg.attack_rate:
                continue
            score = rng.gauss(cfg.separation, 1.0)
            if score >= t:
                outcome = "blue"
                break
            if rng.random() < cfg.attack_success:
                outcome = "red"
                break
        blue += outcome == "blue"
    return blue / episodes


def best_attack_rate(cfg: Config, grid: int = 200) -> tuple[float, float]:
    """Red team picks the attack rate that minimises safety."""
    best = (cfg.attack_rate, 1.0)
    for i in range(1, grid + 1):
        rate = 10 ** (-4 + 3 * i / grid)  # 1e-4 .. 1e-1
        s = safety_analytic(Config(cfg.n_tasks, rate, cfg.audit_budget,
                                   cfg.separation, cfg.attack_success))
        if s < best[1]:
            best = (rate, s)
    return best


if __name__ == "__main__":
    # NOTE: in this simple 'race' model, once the attacker attacks often enough
    # that at least one attack is near-certain, safety no longer depends on the
    # attack rate (it tends to c / (c + s)). The rate columns below show that.
    rates = (0.0001, 0.001, 0.01, 0.05)
    print("audit_budget  separation  " + "  ".join(f"rate={r:<6}" for r in rates))
    for sep in (1.0, 2.0, 3.0):
        for b in (0.005, 0.01, 0.02, 0.05, 0.10):
            row = [safety_analytic(Config(attack_rate=r, audit_budget=b, separation=sep))
                   for r in rates]
            print(f"{b:>12.3f}  {sep:>10.1f}  " + "  ".join(f"{v:>11.3f}" for v in row))
