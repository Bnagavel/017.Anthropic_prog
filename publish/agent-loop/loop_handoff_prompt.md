# Handoff prompt: 010.AutoHex_loop

Paste everything below the line into the new session.

---

## Context

Workspace: `<WORKSPACE>/016.24x7_Agent`.
Core library & Single Source of Truth: `<WORKSPACE>/` (hex-mesh generation from STEP files, core codebase at `<WORKSPACE>/src\hexprep`).
Loop folder: `<WORKSPACE>/016.24x7_Agent\010.AutoHex_loop` (orchestration, mobile polling, and test runner only; mirror folders `slothex_mirror`, `hexprep_mirror`, and local `src/` were deleted; loose CAD/mesh experiment scripts were archived to `<WORKSPACE>/archive\loop_experiments\`).
Python for all runs: `<WORKSPACE>/.venv\Scripts\python.exe`. Run commands in the sandbox first.

## Intention of the loop folder

The loop folder is a 24x7 agent harness around AutoHex.
- **Discord integration**: `discord_mailbox.py` and `run_discord_mailbox.bat` poll Discord. Inbound replies go to the inbox. Updates go out through `logs/outbox.json` (`request_id`, `delivered`, `image_path`). The outbox is the mobile-reply channel. Note: all legacy mirror sync code has been stripped from `discord_mailbox.py`.
- **Dispatcher and model router**: `model_router.py` and `logs/router_state.json` choose the model per task. They work in tiers.
  - Argon (`Gemini 4 Argon`) is the active router and solver when its quota is available.
  - Gemini 3.8 Flash is the fallback receiver when Argon's weekly quota is low.
  - Claude subscription models (`agy-sonnet`, `agy-opus`, `agy-gpt`, and the CLI `claude-sonnet`, `claude-opus`, `claude-haiku`) take complex algorithm work.
  - After a task, or when quota runs out, the router should revert to the Flash receiver.
- **Test harness & single codebase**: `run_decompose_test.py`, `render_mesh.py`, and the `logs/*.msh|png` outputs run against `<WORKSPACE>/src\hexprep` via host Python. No mirrors or duplicate code trees exist.

**Rule:** the core engine in `<WORKSPACE>/src\hexprep\` must stay model-agnostic. That means no hardcoded CAD dimensions, axes, or model names. Decisions must come from geometric or topological invariants.

## Status (as of 2026-11-08)

- **Clean Single Source of Truth**: All core algorithm improvements reside directly in `<WORKSPACE>/src\hexprep`. Redundant mirrors (`slothex_mirror`, `hexprep_mirror`, `010.AutoHex_loop/src/`) and mirror sync routines have been completely removed. `010.AutoHex` can be developed and executed independently at any time.
- Router state was set to Argon at 100% quota, with nothing pinned.
- **Model #7 `p2_flanged_bearing_housing`** (`phase_2/Flanged Bearing Housing.STEP`) now passes all gates: `decompose_sweep`, 18,431 Hex8, coverage 99.94% (was 149.35%), minSJ 0.4632 (was -0.0947), maxAR 5.46, 0 inversions (was 40). Artifacts are `logs/p2_flanged_bearing_housing.msh` and `.png`.
- Fixes applied (all model-agnostic):
  - `sweep_detector.find_antiparallel_pairs`: only planar faces can form sweep cap pairs.
  - `brep_graph._analyze_block`: the degraded-box fallback applies only if `block_vol >= 0.85*bbox_vol`.
  - `brep_graph._merge_sweepable_blocks`: non-box sub-solids are not re-fused.
  - `brep_graph.structural_decompose`: adds axial cut planes where transverse cylinders terminate inside the coaxial solid's span.
  - `sweep_mesher.sweep_extrude_mesh`: falls back to a midpoint cross-section extrusion when lofting produces inversions or a low Jacobian.
  - `multiblock_mesher.mesh_constrained_annulus`: right-handed winding check.
  - `strategy_orchestrator`: prefers sweep for non-box sub-solids, guards fallbacks with minSJ < 0.15, and guards interface snapping and remesh retries.
- Outbox: `flanged_housing_refined_01` was written to `logs/outbox.json` with `delivered: false`. Check that the Discord poller actually delivered it.

### Known issues to check first
1. `logs/model_queue.json` was **not found**, so the Model #7 "passed" status and metrics were never recorded in a queue file. Locate the real queue file, or recreate it, and record the result.
2. Discord polling has shown `getaddrinfo failed` and timeout warnings. These are network or DNS problems on the host.
3. Earlier, the dispatcher on Flash did not wake up reliably for new Discord messages. This is the "hot update" gap. The wake-up path from the mailbox to the agent session needs review.
4. All subagents and background tasks were stopped by a server restart. Restart whatever is still needed.

## Refinement plan (not started)

1. **Fillet junction strategy for `p2_flanged_bearing_housing`**. It should work like the `p2_simple_slotted_l_bracket` fillet detection, but in a model-agnostic way.
   - Detect the concave blend face (cylindrical, toroidal, or variable-radius) that is tangent-continuous to two neighbouring faces.
   - Split at the blend's tangent boundary curves so the fillet becomes its own sub-solid.
   - Classify the fillet sub-solid and mesh it as a radial sweep or annular O-grid, with at least 2 layers across the radius.
   - Take interface layer counts from arc length divided by `target_size`, and share the interface nodes with the barrel and flange. Reuse the `_phase_c` interface alignment.
   - Gate: 0 inversions, minSJ >= 0.15, coverage >= 90%. Otherwise fall back to the current path.
2. **Symmetry identification** in a new `symmetry_detector.py` returning `SymmetryInfo(kind, axes, planes, n)`, called before `structural_decompose`.
   - Detect candidates from the inertia principal axes and test them by B-rep face matching, with reflection tested first.
   - Classes and strategies:

     | Class | Split | Mesh | Boolean |
     |---|---|---|---|
     | Mirror | cut on the plane and mesh half | mirror nodes and flip winding | none |
     | Multi-mirror | quadrant or octant | mesh one cell and mirror | none |
     | Cyclic C_n | n-sector wedge | mesh one sector and rotate | none |
     | Axisymmetric | none, or a few sectors | O-grid with a radial sweep | none |
     | Prismatic | none | sweep | none |
     | Asymmetric | current decomposition | current path | current path |

   - Use symmetry only if the mesh on the symmetry plane is conformal. It is an optimisation and never overrides the quality gates.
3. Implement the fillet strategy first, then mirror and cyclic symmetry. Regression-test on every `p2_*` model. All modifications are made directly in `<WORKSPACE>/src\hexprep` (the single source of truth).

## Constraints
- Keep the core engine model-agnostic.
- Preserve existing comments and docstrings that are unrelated to your change.
- Run commands in the sandbox first.
- Use clickable `file:///` links when referring to files.
