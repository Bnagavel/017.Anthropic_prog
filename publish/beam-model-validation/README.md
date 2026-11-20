# Synthetic Beam Model Training & Analytical Validation

> [!NOTE]
> Shared as a private portfolio example on request. Contains synthetic textbook mechanics data only (simply supported beams with point and distributed loads).

A proof-of-concept pipeline for generating synthetic Euler–Bernoulli simply-supported beam problems, LoRA fine-tuning a small causal language model (`microsoft/DialoGPT-small`), and validating numeric model predictions against closed-form analytical solutions.

## Contents

| File / Folder | Purpose |
|---|---|
| `beam_analysis_data.py` | Synthetic beam problem generator (`BeamAnalysisGenerator`) with closed-form reference reactions, moments, bending stress, deflection, and safety factor |
| `beam_model_training.py` | LoRA fine-tuning pipeline (`BeamAnalysisDataProcessor`, `BeamAnalysisModel`) around `transformers` + `peft` (CLI `__main__` generates a 100-row sample to `./beam_training_data.csv`) |
| `beam_validation.py` | Closed-form verification suite (`BeamAnalyticalSolver`, benchmark problems, `run_validation_example()` demo with a mock inference callable) |
| `beam_api.py`, `test_api.py`, `test_server.py` | Local FastAPI inference wrapper and endpoint smoke checks |
| `run_quickstart.py` | Defensive quickstart runner using `configs/train.poc.yaml` and `configs/validate.poc.yaml` (reads `data/beam_training_data.csv`) |
| `configs/` | `train.poc.yaml` and `validate.poc.yaml` proof-of-concept settings |
| `data/beam_training_data.csv` | Primary synthetic dataset referenced by `configs/train.poc.yaml` and `configs/validate.poc.yaml` (724 KB) |
| `beam_training_data.csv` | Earlier smaller synthetic sample (366 KB) used when invoking `beam_model_training.py` directly |
| `implementation_guide.md` | Detailed architecture and setup guide |
| `requirements.txt` | Python dependencies (`torch`, `transformers`, `peft`, `fastapi`, etc.) |

## Quick Check (Validation Demo)

```bash
pip install numpy pandas scipy matplotlib
python beam_validation.py
```

Running `beam_validation.py` executes `run_validation_example()` against a simple mock model output to verify the closed-form scoring harness without needing GPU weights or network downloads.
