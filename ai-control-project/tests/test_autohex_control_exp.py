import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from autohex_control_exp import run_experiment  # noqa: E402


def test_autohex_experiment_sanity():
    honest, attacks, primary, _ = run_experiment(budget=0.05, save_outputs=False)
    assert len(honest) == 15
    assert len(attacks) == 15

    hon_z = np.array([d.z_score for d in honest])
    assert abs(float(np.mean(hon_z))) < 1e-6
    assert abs(float(np.std(hon_z, ddof=0)) - 1.0) < 1e-6

    assert primary["sep_measured"] > 1.0
    assert 0.0 < primary["safety_gauss"] <= 1.0
    assert 0.0 < primary["safety_emp"] <= 1.0


def test_snapshot_mode_reproduces_frozen_results():
    honest, attacks, primary, _ = run_experiment(budget=0.05, save_outputs=False, snapshot=True)
    assert len(honest) == 15 and len(attacks) == 15
    assert abs(primary["sep_measured"] - 2.202) < 0.01
    assert abs(primary["p_ok_measured"] - 0.6) < 1e-9
    assert abs(primary["safety_emp"] - 11 / 12) < 1e-9
