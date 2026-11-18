"""Deterministic F&DT Engineering Calculation Engine as specified in ARCHITECTURE.md §2 & §4."""

from __future__ import annotations

import math
from fdt_localai.domain.models import Provenance, Quantity
from fdt_localai.domain.units import convert_value


def compute_margin_of_safety(
    applied_stress: Quantity,
    allowable_stress: Quantity,
    scatter_factor: float = 1.0,
) -> Quantity:
    """Compute Margin of Safety: MS = Allowable / (SF * Applied) - 1.

    Automatically converts allowable_stress into the unit of applied_stress
    before computing the dimensionless ratio.
    """
    if scatter_factor <= 0:
        raise ValueError("scatter_factor must be > 0")
    allowable_in_applied_unit = convert_value(
        allowable_stress.value, allowable_stress.unit, applied_stress.unit
    )
    denom = scatter_factor * applied_stress.value
    if abs(denom) < 1e-12:
        ms_val = float("inf")
    else:
        ms_val = (allowable_in_applied_unit / denom) - 1.0
    prov = Provenance(
        file_sha256=applied_stress.provenance.file_sha256,
        file_name=applied_stress.provenance.file_name,
        locator=f"MS({applied_stress.provenance.locator}, {allowable_stress.provenance.locator})",
        extractor="calc_engine.compute_margin_of_safety",
        extractor_version="1.0.0",
    )
    return Quantity(value=ms_val, unit="dimensionless", provenance=prov)


def compute_resultant_load(fx: float, fy: float) -> float:
    """Compute resultant bearing load FBRG = SQRT(FX^2 + FY^2)."""
    return math.hypot(fx, fy)


def compute_max_principal_and_angle(
    sx: float, sy: float, sxy: float
) -> tuple[float, float, float]:
    """Compute plane-stress principal stresses (sigma_max, sigma_min) and angle theta_p (deg)."""
    avg = 0.5 * (sx + sy)
    radius = math.hypot(0.5 * (sx - sy), sxy)
    s_max = avg + radius
    s_min = avg - radius
    theta_rad = 0.5 * math.atan2(2.0 * sxy, sx - sy)
    theta_deg = math.degrees(theta_rad)
    return s_max, s_min, theta_deg
