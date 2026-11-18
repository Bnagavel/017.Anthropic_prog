"""Canonical Engineering Data Model (Pydantic v2) as specified in ARCHITECTURE.md §4."""

from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, Field


def compute_file_sha256(path: Path | str) -> str:
    """Compute SHA-256 hex digest of a file for provenance tracking."""
    p = Path(path)
    if not p.exists() or not p.is_file():
        return "0" * 64
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


class Provenance(BaseModel):
    """First-class provenance record carried by every extracted or computed value."""

    file_sha256: str = Field(..., description="SHA-256 digest of source file")
    file_name: str = Field(..., description="Source file basename or relative path")
    locator: str = Field(
        ...,
        description="Exact location, e.g. 'p.142 L18' | 'Sheet1!D24' | 'line 212'",
    )
    extractor: str = Field(..., description="Ingestion plugin or engine name")
    extractor_version: str = Field(default="1.0.0", description="Plugin version")


class Quantity(BaseModel):
    """Engineering quantity with explicit unit and provenance."""

    value: float
    unit: str = Field(
        ...,
        description="Unit string, e.g. 'MPa', 'ksi', 'psi', 'kN', 'lbf', 'cycles', 'mm', 'in', 'dimensionless'",
    )
    provenance: Provenance


class StructuralLocation(BaseModel):
    """Canonical structural location or spectrum channel."""

    canonical_id: str = Field(..., description="e.g. '11.HM_LHmfs4' or 'RIB4_LF_E10423'")
    aliases: list[str] = Field(default_factory=list)
    component: str | None = None
    material: str | None = None


class LoadCase(BaseModel):
    """Canonical load case or spectrum block definition."""

    canonical_id: str
    aliases: list[str] = Field(default_factory=list)
    category: Literal["limit", "ultimate", "fatigue", "dt", "test", "other"] = "fatigue"


class Result(BaseModel):
    """Canonical engineering result record."""

    result_id: str = Field(default="")
    location_id: str
    load_case_id: str | None = None
    kind: Literal[
        "stress",
        "life",
        "ms",
        "kt",
        "crack_size",
        "inspection_threshold",
        "cspec",
        "ffi",
        "force",
        "other",
    ]
    label: str = Field(default="")
    quantity: Quantity
    status: Literal["extracted", "computed", "reviewed", "approved", "rejected"] = (
        "extracted"
    )


class RedFlag(BaseModel):
    """Deterministic engineering rule check / red flag finding."""

    rule_id: str
    severity: Literal["INFO", "WARNING", "CRITICAL"]
    location_id: str | None = None
    message: str
    provenance: Provenance | None = None


class IngestContext(BaseModel):
    """Context supplied to ingestion plugins."""

    project_id: str = "default"
    default_unit: str = "ksi"
    workspace_dir: str = "workspace"
    options: dict[str, Any] = Field(default_factory=dict)


class IngestResult(BaseModel):
    """Standardised output of any IngestionPlugin."""

    plugin_name: str
    plugin_version: str
    source_path: str
    file_sha256: str
    entities: list[StructuralLocation] = Field(default_factory=list)
    load_cases: list[LoadCase] = Field(default_factory=list)
    results: list[Result] = Field(default_factory=list)
    tables: dict[str, list[dict[str, Any]]] = Field(default_factory=dict)
    text_blocks: list[dict[str, Any]] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    red_flags: list[RedFlag] = Field(default_factory=list)


class RunManifest(BaseModel):
    """Certification-grade reproducibility manifest written with every output."""

    run_id: str
    recipe: str = "spectrum_postprocess@1.0.0"
    code_version: str = "1.0.0"
    created_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    )
    inputs: list[dict[str, str]] = Field(default_factory=list)
    models: dict[str, dict[str, Any]] = Field(default_factory=dict)
    prompts: list[str] = Field(default_factory=list)
    checks: dict[str, Any] = Field(default_factory=dict)
    options: dict[str, Any] = Field(default_factory=dict)
    review: dict[str, str] = Field(
        default_factory=lambda: {
            "state": "extracted",
            "by": "local_engineer",
            "at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        }
    )
