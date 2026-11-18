"""Task Recipe Compiler and Checkpointed DAG Workflow Engine (ARCHITECTURE.md §5 & §6.1)."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from fdt_localai.spectrum.pipeline import (
    SpectrumPipelineOptions,
    SpectrumPipelineOutput,
    run_spectrum_pipeline,
)
from fdt_localai.store.evidence_store import EvidenceStore


@dataclass
class TaskRecipe:
    """Parsed Task Recipe YAML specification."""

    name: str
    version: str
    description: str = ""
    raw_spec: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def load(cls, path: Path | str) -> "TaskRecipe":
        p = Path(path)
        data = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
        return cls(
            name=str(data.get("recipe", p.stem)),
            version=str(data.get("version", "1.0.0")),
            description=str(data.get("description", "")),
            raw_spec=data,
        )


class WorkflowEngine:
    """Executes Task Recipes deterministically and checkpoints job state in SQLite."""

    def __init__(self, store: EvidenceStore | None = None) -> None:
        self.store = store or EvidenceStore()

    def execute_spectrum_recipe(
        self,
        opts: SpectrumPipelineOptions,
        recipe_path: Path | str = "recipes/spectrum_postprocess.yaml",
    ) -> SpectrumPipelineOutput:
        recipe = (
            TaskRecipe.load(recipe_path)
            if Path(recipe_path).exists()
            else TaskRecipe(name="spectrum_postprocess", version="1.0.0")
        )
        job_id = f"job_{opts.base_sheet_name}"
        self.store.create_job(
            job_id=job_id,
            recipe=f"{recipe.name}@{recipe.version}",
            folder_path=opts.folder_path,
        )
        out = run_spectrum_pipeline(opts)
        if out.run_manifest:
            self.store.save_manifest(out.run_manifest)
        self.store.complete_job(
            job_id=job_id,
            output_excel_path=out.excel_path,
            summary={
                "elapsed_seconds": out.elapsed_seconds,
                "nrang_count": len(out.nrang_files),
                "gag_count": len(out.gag_records),
                "cspec_count": len(out.cspec_results),
            },
        )
        return out
