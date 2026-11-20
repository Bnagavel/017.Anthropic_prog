# Surrogate Modelling for Lightning Strike Damage in Composite Laminates

> [!NOTE]
> **This repository is made public only to share a glimpse of my PhD work.** It contains **pseudocode and algorithm descriptions only**, not source code, data or FE models, because the research is unpublished and still under examination at Queen's University Belfast. Full methods and results will appear in my thesis.

## Context
PhD project: *Simulation Tools for the Design of Lightning Strike Protection Solutions*.
High-fidelity coupled electric-thermal (Joule heating) FE simulations of lightning damage in composite laminates are too slow for repeated design studies. The work builds surrogate models that predict damage area from specimen geometry (plate length, width, top-ply angle).

## Contents
| File | Content |
|---|---|
| [algorithms/01_workflow.md](algorithms/01_workflow.md) | End-to-end workflow: design of experiments, FE runs, post-processing |
| [algorithms/02_surrogate_fitting.md](algorithms/02_surrogate_fitting.md) | Polynomial, GAM, GPR and SVR comparison procedure and tuning |
| [algorithms/03_validation.md](algorithms/03_validation.md) | Held-out validation and physical-plausibility checks |

## Status
Work in progress. Quadratic models describe moderate damage area well. Severe damage area is harder, and the GPR/SVR comparison is still being finalised.

## Licence
The documents are released under the MIT licence (see `LICENSE`). The research results, thesis text, data and code are not part of this repository and remain the author's work. Contact: Baskaran Nagavel, Queen's University Belfast.
