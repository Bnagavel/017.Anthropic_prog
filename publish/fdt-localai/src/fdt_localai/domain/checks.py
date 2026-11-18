"""Deterministic Rule & Red-Flag Checks as specified in ARCHITECTURE.md §4.2 & §5."""

from __future__ import annotations

from fdt_localai.domain.models import RedFlag, Result


def run_all_checks(
    results: list[Result],
    min_scatter_factor: float = 1.15,
    expected_stress_unit: str | None = None,
) -> list[RedFlag]:
    """Run standard F&DT engineering checks over a list of canonical Results."""
    flags: list[RedFlag] = []

    for res in results:
        # 1. Missing provenance check
        if (
            not res.quantity.provenance.file_name
            or not res.quantity.provenance.locator
            or res.quantity.provenance.file_sha256 == ""
        ):
            flags.append(
                RedFlag(
                    rule_id="missing_provenance",
                    severity="CRITICAL",
                    location_id=res.location_id,
                    message=f"Result '{res.label or res.kind}' at '{res.location_id}' is missing provenance metadata.",
                    provenance=res.quantity.provenance,
                )
            )

        # 2. Unknown unit check
        if res.kind in ("stress", "force", "cspec", "ffi") and res.quantity.unit in (
            "",
            "unknown",
        ):
            flags.append(
                RedFlag(
                    rule_id="unit_consistency",
                    severity="WARNING",
                    location_id=res.location_id,
                    message=f"Result '{res.label or res.kind}' at '{res.location_id}' has unknown unit.",
                    provenance=res.quantity.provenance,
                )
            )

        if (
            expected_stress_unit
            and res.kind in ("stress", "cspec", "ffi")
            and res.quantity.unit.lower() != expected_stress_unit.lower()
        ):
            flags.append(
                RedFlag(
                    rule_id="unit_consistency",
                    severity="WARNING",
                    location_id=res.location_id,
                    message=(
                        f"Unit mismatch at '{res.location_id}': got '{res.quantity.unit}', "
                        f"expected '{expected_stress_unit}'."
                    ),
                    provenance=res.quantity.provenance,
                )
            )

        # 3. Negative Margin of Safety check
        if res.kind == "ms" and res.quantity.value < 0.0:
            flags.append(
                RedFlag(
                    rule_id="negative_ms",
                    severity="CRITICAL",
                    location_id=res.location_id,
                    message=f"Negative Margin of Safety (MS = {res.quantity.value:.4f}) at '{res.location_id}'.",
                    provenance=res.quantity.provenance,
                )
            )

        # 4. Low scatter factor check
        if (
            res.kind == "other"
            and "scatter" in res.label.lower()
            and res.quantity.value < min_scatter_factor
        ):
            flags.append(
                RedFlag(
                    rule_id="low_scatter_factor",
                    severity="WARNING",
                    location_id=res.location_id,
                    message=(
                        f"Scatter Factor ({res.quantity.value:.3f}) at '{res.location_id}' "
                        f"is below minimum threshold ({min_scatter_factor:.3f})."
                    ),
                    provenance=res.quantity.provenance,
                )
            )

    return flags
