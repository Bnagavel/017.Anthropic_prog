"""Domain layer exports."""

from fdt_localai.domain.calc_engine import (
    compute_margin_of_safety,
    compute_max_principal_and_angle,
    compute_resultant_load,
)
from fdt_localai.domain.checks import run_all_checks
from fdt_localai.domain.entity_resolver import EntityResolver
from fdt_localai.domain.models import (
    IngestContext,
    IngestResult,
    LoadCase,
    Provenance,
    Quantity,
    RedFlag,
    Result,
    RunManifest,
    StructuralLocation,
    compute_file_sha256,
)
from fdt_localai.domain.units import (
    DimensionalityError,
    assert_compatible_units,
    convert_quantity,
    convert_value,
    get_dimension,
)

__all__ = [
    "DimensionalityError",
    "EntityResolver",
    "IngestContext",
    "IngestResult",
    "LoadCase",
    "Provenance",
    "Quantity",
    "RedFlag",
    "Result",
    "RunManifest",
    "StructuralLocation",
    "assert_compatible_units",
    "compute_file_sha256",
    "compute_margin_of_safety",
    "compute_max_principal_and_angle",
    "compute_resultant_load",
    "convert_quantity",
    "convert_value",
    "get_dimension",
    "run_all_checks",
]
