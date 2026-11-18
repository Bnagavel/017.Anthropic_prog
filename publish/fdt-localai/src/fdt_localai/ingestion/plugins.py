"""Ingestion Plugin Contract & Registry as specified in ARCHITECTURE.md §3.1, §3.2, §3.4."""

from __future__ import annotations

from pathlib import Path
from typing import Protocol, runtime_checkable

import openpyxl

from fdt_localai.domain.models import (
    IngestContext,
    IngestResult,
    Provenance,
    Quantity,
    RedFlag,
    Result,
    StructuralLocation,
    compute_file_sha256,
)
from fdt_localai.spectrum.cspec_engine import evaluate_rang_cspec_ffi
from fdt_localai.spectrum.nrang_engine import parse_nrang_file
from fdt_localai.spectrum.project_file_engine import audit_project_file
from fdt_localai.spectrum.rpt_to_elfo import parse_elfo_file, parse_patran_rpt


@runtime_checkable
class IngestionPlugin(Protocol):
    """Protocol implemented by all deterministic file parsers."""

    name: str
    version: str

    def sniff(self, path: Path) -> float: ...
    def parse(self, path: Path, ctx: IngestContext) -> IngestResult: ...


class NrangOutPlugin:
    """Ingestion plugin for SPECTRUM `.nrang.out` files."""

    name = "SPECTRUM_nrang_out"
    version = "1.0.0"

    def sniff(self, path: Path) -> float:
        return 0.99 if path.name.lower().endswith(".nrang.out") else 0.0

    def parse(self, path: Path, ctx: IngestContext) -> IngestResult:
        sha = compute_file_sha256(path)
        nf = parse_nrang_file(path)
        loc = StructuralLocation(
            canonical_id=nf.series_name,
            aliases=[nf.file_name, nf.series_name],
        )
        results: list[Result] = []
        if nf.rows:
            max_s = float(max(nf.switched_1_arr.max(), nf.switched_2_arr.max()))
            min_s = float(min(nf.switched_1_arr.min(), nf.switched_2_arr.min()))
            results.append(
                Result(
                    result_id=f"{nf.series_name}_nrang_max",
                    location_id=nf.series_name,
                    kind="stress",
                    label="max_switched_stress",
                    quantity=Quantity(
                        value=max_s,
                        unit=ctx.default_unit,
                        provenance=Provenance(
                            file_sha256=sha,
                            file_name=nf.file_name,
                            locator=f"Lines 4..{len(nf.rows) + 3}",
                            extractor=self.name,
                            extractor_version=self.version,
                        ),
                    ),
                )
            )
            results.append(
                Result(
                    result_id=f"{nf.series_name}_nrang_min",
                    location_id=nf.series_name,
                    kind="stress",
                    label="min_switched_stress",
                    quantity=Quantity(
                        value=min_s,
                        unit=ctx.default_unit,
                        provenance=Provenance(
                            file_sha256=sha,
                            file_name=nf.file_name,
                            locator=f"Lines 4..{len(nf.rows) + 3}",
                            extractor=self.name,
                            extractor_version=self.version,
                        ),
                    ),
                )
            )
        return IngestResult(
            plugin_name=self.name,
            plugin_version=self.version,
            source_path=str(path),
            file_sha256=sha,
            entities=[loc],
            results=results,
        )


class RangOutPlugin:
    """Ingestion plugin for SPECTRUM `.rang.out` range-paired spectrum files."""

    name = "SPECTRUM_rang_out"
    version = "1.0.0"

    def sniff(self, path: Path) -> float:
        low = path.name.lower()
        return 0.99 if (low.endswith(".rang.out") and not low.endswith(".nrang.out")) else 0.0

    def parse(self, path: Path, ctx: IngestContext) -> IngestResult:
        sha = compute_file_sha256(path)
        cr = evaluate_rang_cspec_ffi(path)
        loc = StructuralLocation(
            canonical_id=cr.location,
            aliases=[cr.file_name, cr.location],
        )
        prov = Provenance(
            file_sha256=sha,
            file_name=cr.file_name,
            locator=f"GAG Line {cr.x900_max_line}/{cr.x900_min_line}",
            extractor=self.name,
            extractor_version=self.version,
        )
        results = [
            Result(
                result_id=f"{cr.location}_ffi",
                location_id=cr.location,
                kind="ffi",
                label="fFI",
                quantity=Quantity(value=cr.ffi, unit=ctx.default_unit, provenance=prov),
            ),
            Result(
                result_id=f"{cr.location}_cspec",
                location_id=cr.location,
                kind="cspec",
                label="CSPEC",
                quantity=Quantity(value=cr.cspec, unit=ctx.default_unit, provenance=prov),
            ),
            Result(
                result_id=f"{cr.location}_x900_max",
                location_id=cr.location,
                kind="stress",
                label="X900_GAG_Max",
                quantity=Quantity(
                    value=cr.x900_max, unit=ctx.default_unit, provenance=prov
                ),
            ),
        ]
        return IngestResult(
            plugin_name=self.name,
            plugin_version=self.version,
            source_path=str(path),
            file_sha256=sha,
            entities=[loc],
            results=results,
        )


class ProjectFilePlugin:
    """Ingestion plugin for SPECTRUM `project_file`."""

    name = "SPECTRUM_project_file"
    version = "1.0.0"

    def sniff(self, path: Path) -> float:
        return 0.98 if path.name.lower().startswith("project_file") else 0.0

    def parse(self, path: Path, ctx: IngestContext) -> IngestResult:
        sha = compute_file_sha256(path)
        audit = audit_project_file(path)
        warnings = [
            f["message"]
            for f in audit.get("findings", [])
            if f.get("severity") in ("WARNING", "ERROR")
        ]
        return IngestResult(
            plugin_name=self.name,
            plugin_version=self.version,
            source_path=str(path),
            file_sha256=sha,
            tables={"audit_findings": audit.get("findings", [])},
            warnings=warnings,
        )


class PatranRptPlugin:
    """Ingestion plugin for Patran `.rpt` load files."""

    name = "patran_rpt"
    version = "1.0.0"

    def sniff(self, path: Path) -> float:
        return 0.95 if path.name.lower().endswith(".rpt") else 0.0

    def parse(self, path: Path, ctx: IngestContext) -> IngestResult:
        sha = compute_file_sha256(path)
        deck = parse_patran_rpt(path)
        entities = [
            StructuralLocation(canonical_id=f"ELEM_{r.elem_id}_{r.typ}")
            for r in deck.rows
        ]
        return IngestResult(
            plugin_name=self.name,
            plugin_version=self.version,
            source_path=str(path),
            file_sha256=sha,
            entities=entities,
            warnings=deck.warnings,
        )


class ElfoDeckPlugin:
    """Ingestion plugin for SPECTRUM `.elfo` and `.endl` files."""

    name = "SPECTRUM_elfo"
    version = "1.0.0"

    def sniff(self, path: Path) -> float:
        return 0.95 if path.name.lower().endswith((".elfo", ".endl")) else 0.0

    def parse(self, path: Path, ctx: IngestContext) -> IngestResult:
        sha = compute_file_sha256(path)
        deck = parse_elfo_file(path)
        entities = [
            StructuralLocation(canonical_id=f"ELEM_{r.elem_id}_{r.typ}")
            for r in deck.rows
        ]
        return IngestResult(
            plugin_name=self.name,
            plugin_version=self.version,
            source_path=str(path),
            file_sha256=sha,
            entities=entities,
            warnings=deck.warnings,
        )


class ExcelCalcPlugin:
    """Ingestion plugin for `.xlsx`/`.xlsm` calculation sheets (ARCHITECTURE.md §3.4).

    Never executes macros (`keep_vba=False`) and detects uncached/stale formulas (`UNCACHED`).
    """

    name = "excel_calc"
    version = "1.0.0"

    def sniff(self, path: Path) -> float:
        return 0.90 if path.name.lower().endswith((".xlsx", ".xlsm")) else 0.0

    def parse(self, path: Path, ctx: IngestContext) -> IngestResult:
        sha = compute_file_sha256(path)
        wb_f = openpyxl.load_workbook(path, data_only=False, read_only=True)
        wb_v = openpyxl.load_workbook(path, data_only=True, read_only=True)

        warnings: list[str] = []
        red_flags: list[RedFlag] = []
        for s_name in wb_f.sheetnames[:5]:
            ws_f = wb_f[s_name]
            ws_v = wb_v[s_name]
            for r_idx, (row_f, row_v) in enumerate(
                zip(
                    ws_f.iter_rows(max_row=50, max_col=20, values_only=True),
                    ws_v.iter_rows(max_row=50, max_col=20, values_only=True),
                ),
                start=1,
            ):
                for c_idx, (vf, vv) in enumerate(zip(row_f, row_v), start=1):
                    if isinstance(vf, str) and vf.startswith("=") and vv is None:
                        loc_str = f"{s_name}!{openpyxl.utils.get_column_letter(c_idx)}{r_idx}"
                        warnings.append(f"UNCACHED formula at {loc_str}: {vf}")
                        red_flags.append(
                            RedFlag(
                                rule_id="uncached_excel_formula",
                                severity="WARNING",
                                location_id=s_name,
                                message=f"Formula cell {loc_str} has no cached value (UNCACHED).",
                                provenance=Provenance(
                                    file_sha256=sha,
                                    file_name=path.name,
                                    locator=loc_str,
                                    extractor=self.name,
                                    extractor_version=self.version,
                                ),
                            )
                        )
        wb_f.close()
        wb_v.close()
        return IngestResult(
            plugin_name=self.name,
            plugin_version=self.version,
            source_path=str(path),
            file_sha256=sha,
            warnings=warnings,
            red_flags=red_flags,
        )


class PluginRegistry:
    """Routes files to the highest-confidence `IngestionPlugin`."""

    def __init__(self) -> None:
        self.plugins: list[IngestionPlugin] = [
            NrangOutPlugin(),
            RangOutPlugin(),
            ProjectFilePlugin(),
            PatranRptPlugin(),
            ElfoDeckPlugin(),
            ExcelCalcPlugin(),
        ]

    def get_plugin_for(self, path: Path | str) -> IngestionPlugin | None:
        p = Path(path)
        scored = sorted(
            ((pl.sniff(p), pl) for pl in self.plugins),
            key=lambda x: x[0],
            reverse=True,
        )
        if scored and scored[0][0] > 0.0:
            return scored[0][1]
        return None

    def ingest_file(
        self, path: Path | str, ctx: IngestContext | None = None
    ) -> IngestResult:
        p = Path(path)
        plugin = self.get_plugin_for(p)
        if plugin is None:
            raise ValueError(f"No ingestion plugin matched file: {p}")
        return plugin.parse(p, ctx or IngestContext())
