"""
Run an end-to-end PoC: generate data -> small train -> validate.
The script is defensive: if a step's outputs exist, it skips that step.
"""
import os
import sys
import json
from pathlib import Path

ROOT = Path(__file__).parent
DATA_DIR = ROOT / "data"
CKPT_DIR = ROOT / "checkpoints" / "poc"
LOGS_DIR = ROOT / "logs"
CONFIGS_DIR = ROOT / "configs"

DATA_CSV = DATA_DIR / "beam_training_data.csv"
TRAIN_CFG = CONFIGS_DIR / "train.poc.yaml"
VAL_CFG = CONFIGS_DIR / "validate.poc.yaml"


def ensure_dirs():
    for d in (DATA_DIR, CKPT_DIR, LOGS_DIR):
        d.mkdir(parents=True, exist_ok=True)


def step_data():
    """Generate dataset if missing."""
    if DATA_CSV.exists():
        print(f"[data] Found existing {DATA_CSV}, skipping generation.")
        return
    print("[data] Generating training dataset (small)...")
    try:
        from beam_analysis_data import generate_training_dataset
    except Exception as e:
        print("[data] Missing or invalid beam_analysis_data.py with generate_training_dataset().", file=sys.stderr)
        raise
    # Call with positional arg to support unknown signatures
    df = generate_training_dataset(200)
    df.to_csv(DATA_CSV, index=False)
    print(f"[data] Wrote {DATA_CSV} with {len(df)} rows.")


def _script_exists_and_nonempty(path: Path) -> bool:
    return path.exists() and path.is_file() and path.stat().st_size > 10


def step_train():
    """Run a tiny training; expects beam_model_training.py to read configs/train.poc.yaml.
    If missing or empty, skip gracefully with a message.
    """
    train_script = ROOT / "beam_model_training.py"
    if not _script_exists_and_nonempty(train_script):
        print(f"[train] {train_script.name} missing or empty. Skipping training step.")
        return
    print("[train] Starting tiny training run...")
    exit_code = os.system(f"{sys.executable} {train_script.as_posix()} --config {TRAIN_CFG.as_posix()}")
    if exit_code != 0:
        print("[train] Training returned non-zero exit code. See logs; continuing to validation if available.")


def step_validate():
    """Run validation; expects beam_validation.py to read configs/validate.poc.yaml.
    If missing or empty, skip gracefully with a message.
    """
    val_script = ROOT / "beam_validation.py"
    if not _script_exists_and_nonempty(val_script):
        print(f"[validate] {val_script.name} missing or empty. Skipping validation step.")
        return
    print("[validate] Running validation...")
    exit_code = os.system(f"{sys.executable} {val_script.as_posix()} --config {VAL_CFG.as_posix()}")
    if exit_code != 0:
        print("[validate] Validation returned non-zero exit code. See logs.")


if __name__ == "__main__":
    ensure_dirs()
    step_data()
    step_train()
    step_validate()
    print("[done] Quickstart completed. Check logs/ and checkpoints/poc/")
