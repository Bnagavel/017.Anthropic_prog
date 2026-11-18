"""
Minimal FastAPI API for beam analysis.
- If a trained checkpoint exists, uses the model for inference.
- Otherwise, falls back to an analytical solver for simple cases.

Start locally:
    uvicorn beam_api:app --host 0.0.0.0 --port 8000
"""
from typing import List, Dict, Optional
from pathlib import Path
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import json

# Optional: import torch/transformers only if model exists to keep startup fast
CKPT_DIR = Path("checkpoints/poc")

app = FastAPI(title="Beam Analysis AI API")


class Load(BaseModel):
    type: str  # "point" | "udl" etc.
    magnitude: float
    position: Optional[float] = None  # for point loads


class BeamProblem(BaseModel):
    description: str
    beam_length: float
    loads: List[Load]
    material: str
    support_type: str  # "simply_supported", etc.


class BeamSolution(BaseModel):
    max_stress: float
    max_deflection: float
    safety_factor: float
    analysis_code: str
    report: str


# ---- Simple analytical fallback for simply supported beam with one point load ----
# This is a placeholder; expand as needed for your domain coverage.
def _analytical_solve(problem: BeamProblem) -> BeamSolution:
    L = float(problem.beam_length)
    if not problem.loads:
        raise HTTPException(status_code=400, detail="No loads provided")
    load = problem.loads[0]
    if load.type != "point" or load.position is None:
        raise HTTPException(status_code=400, detail="Analytical fallback supports one point load only")

    P = float(load.magnitude)
    a = float(load.position)
    b = L - a

    # Max bending moment for simply supported beam with a point load at a
    # M_max occurs under the load: M = P*a*b/L
    M_max = P * a * b / L  # N*m

    # Naive section props (placeholder): rectangular section 0.1m x 0.2m
    b_sec = 0.1
    h_sec = 0.2
    I = b_sec * h_sec**3 / 12.0
    y = h_sec / 2.0

    # Bending stress sigma = M*y/I
    sigma_max = M_max * y / I  # Pa

    # Deflection (under load) for point load at a on simply supported beam is more involved;
    # use a simple symmetric case when a=L/2 for placeholder.
    if abs(a - L/2) < 1e-6:
        # delta_max at midspan: P*L^3/(48*E*I)
        E = 200e9  # Pa for steel (placeholder; use material map)
        delta_max = P * L**3 / (48.0 * E * I)
    else:
        # Fallback: approximate with midspan formula for demo purposes
        E = 200e9
        delta_max = P * L**3 / (48.0 * E * I)

    # Safety factor (placeholder): yield of steel A36 ~ 250 MPa
    fy = 250e6
    sf = max(0.1, fy / max(1e-6, sigma_max))

    code = (
        "# Placeholder analysis code\n"
        f"L = {L}; P = {P}; a = {a}; b = {b}\n"
        f"M_max = P*a*b/L\n"
        "# Section props for 0.1x0.2 m rectangle\n"
        "b_sec = 0.1; h_sec = 0.2\n"
        "I = b_sec*h_sec**3/12\n"
        "y = h_sec/2\n"
        "sigma_max = M_max*y/I\n"
        "E = 200e9\n"
        "delta_max = P*L**3/(48*E*I)\n"
    )

    report = (
        "Analytical fallback solution (simplified).\n"
        f"Max bending moment: {M_max:.3e} N*m\n"
        f"Max bending stress: {sigma_max:.3e} Pa\n"
        f"Max deflection: {delta_max:.3e} m\n"
        f"Estimated safety factor: {sf:.2f}\n"
    )

    return BeamSolution(
        max_stress=float(sigma_max),
        max_deflection=float(delta_max),
        safety_factor=float(sf),
        analysis_code=code,
        report=report,
    )


@app.post("/analyze_beam", response_model=BeamSolution)
async def analyze_beam(problem: BeamProblem):
    # TODO: if you have a trained model checkpoint, load and run inference here.
    # For now, use analytical fallback.
    return _analytical_solve(problem)


@app.get("/health")
async def health():
    return {"status": "ok"}
