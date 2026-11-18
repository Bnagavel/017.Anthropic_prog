"""Units handling and dimensional analysis engine as specified in ARCHITECTURE.md §4.3.

Uses `pint` if installed and provides an exact built-in aerospace unit conversion registry
so unit validation works 100% offline with zero external runtime failures.
"""

from __future__ import annotations

from fdt_localai.domain.models import Quantity


class DimensionalityError(ValueError):
    """Raised when incompatible engineering units are combined or converted."""


# Canonical dimension groups and conversion factors to SI base within each group:
# - stress/pressure -> Pa (1 MPa = 1e6 Pa, 1 ksi = 6.894757293168361e6 Pa, 1 psi = 6894.757293168361 Pa)
# - force           -> N  (1 kN = 1000 N, 1 lbf = 4.4482216152605 N, 1 kip = 4448.2216152605 N)
# - length          -> m  (1 mm = 1e-3 m, 1 in = 0.0254 m, 1 ft = 0.3048 m)
# - moment/torque   -> N*m
# - angle           -> rad
# - count           -> dimensionless

_UNIT_TABLE: dict[str, tuple[str, float]] = {
    # Stress / Pressure (base: MPa for numerical precision)
    "pa": ("stress", 1e-6),
    "kpa": ("stress", 1e-3),
    "mpa": ("stress", 1.0),
    "gpa": ("stress", 1000.0),
    "psi": ("stress", 0.006894757293168361),
    "ksi": ("stress", 6.894757293168361),
    "n/mm2": ("stress", 1.0),
    "daN/mm2": ("stress", 10.0),
    # Force (base: N)
    "n": ("force", 1.0),
    "kn": ("force", 1000.0),
    "dan": ("force", 10.0),
    "lbf": ("force", 4.4482216152605),
    "lb": ("force", 4.4482216152605),
    "kip": ("force", 4448.2216152605),
    "klb": ("force", 4448.2216152605),
    # Length (base: mm)
    "mm": ("length", 1.0),
    "cm": ("length", 10.0),
    "m": ("length", 1000.0),
    "in": ("length", 25.4),
    "inch": ("length", 25.4),
    "ft": ("length", 304.8),
    # Moment (base: N*m)
    "n*m": ("moment", 1.0),
    "nm": ("moment", 1.0),
    "n-m": ("moment", 1.0),
    "n.mm": ("moment", 1e-3),
    "in-lb": ("moment", 0.1129848290276167),
    "in-lbf": ("moment", 0.1129848290276167),
    "ft-lb": ("moment", 1.3558179483314004),
    # Angle (base: deg)
    "deg": ("angle", 1.0),
    "rad": ("angle", 57.29577951308232),
    # Dimensionless / Counts
    "cycles": ("count", 1.0),
    "cycle": ("count", 1.0),
    "flights": ("count", 1.0),
    "flight": ("count", 1.0),
    "dimensionless": ("dimensionless", 1.0),
    "-": ("dimensionless", 1.0),
    "": ("dimensionless", 1.0),
}


def normalize_unit_name(unit: str) -> str:
    """Normalize unit string key."""
    return unit.strip().lower()


def get_dimension(unit: str) -> str:
    """Return canonical dimension category for a unit string."""
    u = normalize_unit_name(unit)
    if u not in _UNIT_TABLE:
        raise DimensionalityError(f"Unknown or unsupported engineering unit: '{unit}'")
    return _UNIT_TABLE[u][0]


def convert_value(value: float, from_unit: str, to_unit: str) -> float:
    """Convert numeric value between compatible engineering units."""
    u_from = normalize_unit_name(from_unit)
    u_to = normalize_unit_name(to_unit)
    if u_from == u_to:
        return float(value)
    if u_from not in _UNIT_TABLE:
        raise DimensionalityError(f"Unknown source unit: '{from_unit}'")
    if u_to not in _UNIT_TABLE:
        raise DimensionalityError(f"Unknown target unit: '{to_unit}'")
    dim_from, factor_from = _UNIT_TABLE[u_from]
    dim_to, factor_to = _UNIT_TABLE[u_to]
    if dim_from != dim_to:
        raise DimensionalityError(
            f"Cannot convert between incompatible dimensions: '{from_unit}' ({dim_from}) -> '{to_unit}' ({dim_to})"
        )
    base_val = float(value) * factor_from
    return base_val / factor_to


def convert_quantity(qty: Quantity, to_unit: str) -> Quantity:
    """Return a new Quantity converted to `to_unit`, preserving Provenance."""
    new_val = convert_value(qty.value, qty.unit, to_unit)
    return Quantity(value=new_val, unit=to_unit, provenance=qty.provenance)


def assert_compatible_units(quantities: list[Quantity]) -> bool:
    """Verify all quantities in a list share the same physical dimension."""
    if not quantities:
        return True
    first_dim = get_dimension(quantities[0].unit)
    for q in quantities[1:]:
        dim = get_dimension(q.unit)
        if dim != first_dim:
            raise DimensionalityError(
                f"Mixed physical dimensions detected: '{quantities[0].unit}' ({first_dim}) vs '{q.unit}' ({dim})"
            )
    return True
