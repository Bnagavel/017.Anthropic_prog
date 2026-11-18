"""Job Service & Review/Approval Gate Service (ARCHITECTURE.md §3 & §7)."""

from __future__ import annotations

from typing import Any

from fdt_localai.spectrum.pipeline import (
    SpectrumPipelineOptions,
    SpectrumPipelineOutput,
)
from fdt_localai.store.evidence_store import EvidenceStore
from fdt_localai.workflow.engine import WorkflowEngine


class JobService:
    """Thin-client job submission and approval service backed by SQLite."""

    def __init__(self, store: EvidenceStore | None = None) -> None:
        self.store = store or EvidenceStore()
        self.workflow = WorkflowEngine(self.store)

    def submit_and_run(self, opts: SpectrumPipelineOptions) -> SpectrumPipelineOutput:
        return self.workflow.execute_spectrum_recipe(opts)

    def approve_run(self, run_id: str, reviewer: str = "B.Nagavel") -> None:
        self.store.update_review_state(run_id, "approved", reviewer=reviewer)

    def get_job_status(self, job_id: str) -> dict[str, Any] | None:
        return self.store.get_job(job_id)
