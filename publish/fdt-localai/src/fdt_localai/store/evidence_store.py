"""SQLite WAL-mode Evidence Store as specified in ARCHITECTURE.md §4.4 & §7."""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fdt_localai.domain.models import Result, RunManifest


class EvidenceStore:
    """Persistent SQLite Evidence Store for jobs, results, provenance, and review states."""

    def __init__(self, db_path: Path | str = "workspace/fdt_evidence.sqlite") -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL;")
        return conn

    def _init_schema(self) -> None:
        with self._connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS jobs (
                    job_id TEXT PRIMARY KEY,
                    recipe TEXT NOT NULL,
                    folder_path TEXT NOT NULL,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    output_excel_path TEXT,
                    summary_json TEXT
                );

                CREATE TABLE IF NOT EXISTS results (
                    result_id TEXT PRIMARY KEY,
                    job_id TEXT NOT NULL,
                    location_id TEXT NOT NULL,
                    kind TEXT NOT NULL,
                    label TEXT,
                    value REAL NOT NULL,
                    unit TEXT NOT NULL,
                    status TEXT NOT NULL,
                    provenance_json TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS run_manifests (
                    run_id TEXT PRIMARY KEY,
                    recipe TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    review_state TEXT NOT NULL,
                    reviewed_by TEXT NOT NULL,
                    manifest_json TEXT NOT NULL
                );
                """
            )

    def create_job(self, job_id: str, recipe: str, folder_path: str) -> None:
        now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        with self._connect() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO jobs
                (job_id, recipe, folder_path, status, created_at, updated_at)
                VALUES (?, ?, ?, 'RUNNING', ?, ?)
                """,
                (job_id, recipe, folder_path, now, now),
            )

    def complete_job(
        self,
        job_id: str,
        output_excel_path: str,
        summary: dict[str, Any],
        status: str = "COMPLETED",
    ) -> None:
        now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        with self._connect() as conn:
            conn.execute(
                """
                UPDATE jobs
                SET status = ?, updated_at = ?, output_excel_path = ?, summary_json = ?
                WHERE job_id = ?
                """,
                (status, now, output_excel_path, json.dumps(summary), job_id),
            )

    def save_results(self, job_id: str, results: list[Result]) -> None:
        with self._connect() as conn:
            for r in results:
                rid = r.result_id or f"{job_id}_{r.location_id}_{r.label or r.kind}"
                conn.execute(
                    """
                    INSERT OR REPLACE INTO results
                    (result_id, job_id, location_id, kind, label, value, unit, status, provenance_json)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        rid,
                        job_id,
                        r.location_id,
                        r.kind,
                        r.label,
                        r.quantity.value,
                        r.quantity.unit,
                        r.status,
                        r.quantity.provenance.model_dump_json(),
                    ),
                )

    def save_manifest(self, manifest: RunManifest) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO run_manifests
                (run_id, recipe, created_at, review_state, reviewed_by, manifest_json)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    manifest.run_id,
                    manifest.recipe,
                    manifest.created_at,
                    manifest.review.get("state", "extracted"),
                    manifest.review.get("by", "local_engineer"),
                    manifest.model_dump_json(),
                ),
            )

    def update_review_state(
        self, run_id: str, new_state: str, reviewer: str = "local_engineer"
    ) -> None:
        """Human Approval Gate (`extracted` -> `reviewed` -> `approved`)."""
        if new_state not in ("extracted", "reviewed", "approved", "rejected"):
            raise ValueError(f"Invalid review state: {new_state}")
        with self._connect() as conn:
            row = conn.execute(
                "SELECT manifest_json FROM run_manifests WHERE run_id = ?", (run_id,)
            ).fetchone()
            if row:
                data = json.loads(row["manifest_json"])
                data["review"] = {
                    "state": new_state,
                    "by": reviewer,
                    "at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                }
                conn.execute(
                    """
                    UPDATE run_manifests
                    SET review_state = ?, reviewed_by = ?, manifest_json = ?
                    WHERE run_id = ?
                    """,
                    (new_state, reviewer, json.dumps(data), run_id),
                )

    def get_job(self, job_id: str) -> dict[str, Any] | None:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM jobs WHERE job_id = ?", (job_id,)
            ).fetchone()
            return dict(row) if row else None
