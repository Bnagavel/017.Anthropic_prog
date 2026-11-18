"""Local LLM Gateway (Gemma 2 2B Instruct / Qwen 2.5 7B via local Ollama on 127.0.0.1).

Implements ARCHITECTURE.md §6.3, §6.4, §6.5 & PROJECT_PLAN.md §4.2:
1.Strictly local loopback (`127.0.0.1:11434`) — zero external network calls.
2. Prompt Registry (`prompts/*.md`).
3. Zero-Hallucination Number Verifier: verifies every number in generated prose
   against the deterministic input fact table.
4. OEM Glossary & Style Engine (`config/glossary/oem_a.yaml`).
5. Deterministic engineering prose synthesis fallback when Ollama daemon is offline.
"""

from __future__ import annotations

import json
import re
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any

import yaml

if TYPE_CHECKING:
    from fdt_localai.spectrum.coincident_gag import CoincidentGagRecord
    from fdt_localai.spectrum.cspec_engine import CSpecChannelResult


@dataclass
class GenParams:
    """Reproducible generation parameters for local inference."""

    tier: str = "fast"
    model_name: str = "gemma2:2b-instruct-q4_K_M"
    temperature: float = 0.0
    seed: int = 42
    num_ctx: int = 8192


@dataclass
class LLMResult:
    """Verified output from the LLM Gateway."""

    text: str
    model_used: str
    prompt_id: str
    numbers_verified: bool
    unverified_numbers: list[float] = field(default_factory=list)
    used_deterministic_fallback: bool = False


class NumberVerifier:
    """Zero-Hallucination Guard: ensures every numeric literal in text originates from source facts."""

    _NUM_RE = re.compile(r"(?<![A-Za-z0-9_])[-+]?\d+(?:\.\d+)?(?![A-Za-z0-9_])")

    @classmethod
    def extract_numbers(cls, text: str) -> list[float]:
        """Extract standalone numbers (ignoring tokens like X900, PROGRAM-X, Q01, 7040-T7451)."""
        # Strip protected alphanumeric identifiers before scanning numbers
        cleaned = re.sub(
            r"\b(?:X900|X090|X009|X001|END1|END2|END3|PROGRAM-X|7040-T7451|7050-T7451|Q\d+|EF\(\d+,[A-Za-z]+\)|\d+\.[A-Za-z][A-Za-z0-9_]*)\b",
            " ",
            text,
        )
        nums: list[float] = []
        for m in cls._NUM_RE.finditer(cleaned):
            try:
                nums.append(float(m.group(0)))
            except ValueError:
                continue
        return nums

    @classmethod
    def verify_against_facts(
        cls,
        text: str,
        allowed_numbers: list[float],
        rel_tol: float = 1e-2,
        abs_tol: float = 0.02,
    ) -> tuple[bool, list[float]]:
        """Check that every number in `text` matches at least one number in `allowed_numbers`."""
        extracted = cls.extract_numbers(text)
        unverified: list[float] = []
        for val in extracted:
            matched = any(
                abs(val - ref) <= max(abs_tol, rel_tol * abs(ref))
                for ref in allowed_numbers
            )
            if not matched:
                unverified.append(val)
        return (len(unverified) == 0), unverified


class StyleEngine:
    """Applies OEM glossary terminology rules while protecting engineering identifiers."""

    def __init__(self, glossary_path: Path | str | None = None) -> None:
        self.replacements: dict[str, str] = {
            "safety factor": "Scatter Factor",
            "factor of safety": "Scatter Factor",
        }
        self.protected_tokens: list[str] = [
            "X900",
            "X090",
            "X009",
            "X001",
            "FBRG",
            "CSPEC",
            "fFI",
        ]
        if glossary_path and Path(glossary_path).exists():
            data = yaml.safe_load(Path(glossary_path).read_text(encoding="utf-8")) or {}
            self.replacements.update(data.get("replacements", {}))
            self.protected_tokens = data.get("protected_tokens", self.protected_tokens)

    def apply(self, text: str) -> str:
        """Apply glossary replacements case-insensitively."""
        out = text
        for src, dst in self.replacements.items():
            pattern = re.compile(rf"\b{re.escape(src)}\b", re.IGNORECASE)
            out = pattern.sub(dst, out)
        return out


class LLMGateway:
    """Offline Local LLM Gateway binding strictly to `127.0.0.1:11434`."""

    def __init__(
        self,
        ollama_host: str = "http://127.0.0.1:11434",
        glossary_path: Path | str | None = "config/glossary/oem_a.yaml",
    ) -> None:
        if not (
            ollama_host.startswith("http://127.0.0.1")
            or ollama_host.startswith("http://localhost")
        ):
            raise ValueError(
                f"Security Policy Violation: LLM host must be loopback (127.0.0.1), got {ollama_host}"
            )
        self.ollama_host = ollama_host.rstrip("/")
        self.style_engine = StyleEngine(glossary_path)

    def is_ollama_online(self, timeout: float = 0.8) -> bool:
        """Check if local Ollama service is reachable on 127.0.0.1:11434."""
        req = urllib.request.Request(f"{self.ollama_host}/api/tags", method="GET")
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return resp.status == 200
        except Exception:
            return False

    def generate_oem_comparison_summary(
        self,
        folder_name: str,
        gag_records: list[CoincidentGagRecord],
        cspec_results: list[CSpecChannelResult],
        params: GenParams | None = None,
    ) -> LLMResult:
        """Generate an OEM-style engineering summary of Coincident GAG and C-Spec / fFI results.

        Uses local Gemma 2 2B via Ollama if running, verifies all numbers with `NumberVerifier`,
        and falls back to deterministic OEM template synthesis if Ollama is not running or
        if any number fails verification.
        """
        gen_params = params or GenParams()
        allowed_nums: list[float] = [
            float(len(gag_records)),
            float(len(cspec_results)),
            1.0,
            2.0,
            900.0,
        ]
        for g in gag_records:
            allowed_nums.extend(
                [
                    round(g.x900_gag_max, 4),
                    round(g.x900_gag_min, 4),
                    float(g.max_mission_line),
                    float(g.min_mission_line),
                    round(g.coincident_col_1, 4),
                    round(g.coincident_col_2, 4),
                    round(g.resultant_or_maxp, 4),
                    round(g.delta_check, 4),
                ]
            )
        for c in cspec_results:
            allowed_nums.extend(
                [
                    round(c.ffi, 4),
                    round(c.ffi, 2),
                    round(c.cspec, 4),
                    round(c.cspec, 2),
                    round(c.x900_max, 4),
                    round(c.x900_min, 4),
                    round(c.x900_max_over_ffi, 4),
                    round(c.x900_cycle_ffi, 4),
                    round(c.x900_cycle_ffi_ratio, 4),
                    round(c.x900_cycle_ffi_ratio * 100.0, 2),
                    float(c.x900_max_line),
                    float(c.x900_min_line),
                ]
            )

        deterministic_prose = self._build_deterministic_summary(
            folder_name, gag_records, cspec_results
        )

        if self.is_ollama_online():
            facts = {
                "dataset": folder_name,
                "channel_count": len(cspec_results) or len(gag_records),
                "cspec_summary": [
                    {
                        "location": c.location,
                        "fFI": round(c.ffi, 4),
                        "CSPEC": round(c.cspec, 4),
                        "x900_max": round(c.x900_max, 4),
                        "x900_min": round(c.x900_min, 4),
                    }
                    for c in cspec_results
                ],
                "gag_summary": [
                    {
                        "location": g.location,
                        "x900_gag_max": round(g.x900_gag_max, 4),
                        "mission_line": g.max_mission_line,
                        "endpoint": g.max_endpoint,
                        "status": g.status,
                    }
                    for g in gag_records
                ],
            }
            prompt = (
                "Write a concise OEM aerospace fatigue spectrum comparison paragraph "
                "using ONLY the exact numbers in this JSON table:\n"
                + json.dumps(facts, indent=2)
            )
            raw_llm_text = self._call_ollama(prompt, gen_params)
            if raw_llm_text:
                styled = self.style_engine.apply(raw_llm_text)
                ok, bad_nums = NumberVerifier.verify_against_facts(styled, allowed_nums)
                if ok:
                    return LLMResult(
                        text=styled,
                        model_used=gen_params.model_name,
                        prompt_id="narrate_comparison@v1",
                        numbers_verified=True,
                        used_deterministic_fallback=False,
                    )

        styled_det = self.style_engine.apply(deterministic_prose)
        ok_det, bad_det = NumberVerifier.verify_against_facts(styled_det, allowed_nums)
        return LLMResult(
            text=styled_det,
            model_used=f"{gen_params.model_name} (Deterministic Verified Engine)",
            prompt_id="narrate_comparison@v1",
            numbers_verified=ok_det,
            unverified_numbers=bad_det,
            used_deterministic_fallback=True,
        )

    def _build_deterministic_summary(
        self,
        folder_name: str,
        gag_records: list[CoincidentGagRecord],
        cspec_results: list[CSpecChannelResult],
    ) -> str:
        """Synthesize an OEM-style engineering comparison summary from verified facts."""
        lines: list[str] = [
            f"OEM SPECTRUM SEVERITY & COINCIDENT GAG EVALUATION SUMMARY ({folder_name})",
            "-" * 78,
        ]
        if cspec_results:
            max_ffi_ch = max(cspec_results, key=lambda x: x.ffi)
            min_ffi_ch = min(cspec_results, key=lambda x: x.ffi)
            max_cspec_ch = max(cspec_results, key=lambda x: x.cspec)
            lines.append(
                f"1. Spectrum Severity (fFI & C-Spec): The Range-Paired (CRPR) fatigue spectrum "
                f"evaluation was conducted across {len(cspec_results)} structural channels. "
                f"The governing peak Equivalent Fatigue Stress (fFI) occurs at location "
                f"{max_ffi_ch.location} with fFI = {max_ffi_ch.ffi:.4f} (CSPEC = {max_ffi_ch.cspec:.4f}), "
                f"whereas the lowest severity is observed at {min_ffi_ch.location} with "
                f"fFI = {min_ffi_ch.ffi:.4f} (CSPEC = {min_ffi_ch.cspec:.4f}). "
                f"The maximum C-Spec damage index is {max_cspec_ch.cspec:.4f} at {max_cspec_ch.location}."
            )
            lines.append(
                f"2. Ground-Air-Ground (GAG) Contribution: At the critical location {max_ffi_ch.location}, "
                f"the X900 GAG cycle varies between a maximum of {max_ffi_ch.x900_max:.4f} "
                f"(Mission Line {max_ffi_ch.x900_max_line}) and a minimum of {max_ffi_ch.x900_min:.4f} "
                f"(Mission Line {max_ffi_ch.x900_min_line}), contributing an X900_cycle_ffi of "
                f"{max_ffi_ch.x900_cycle_ffi:.4f} ({max_ffi_ch.x900_cycle_ffi_ratio * 100.0:.2f}% of total fFI)."
            )
        if gag_records:
            peak_gag = max(gag_records, key=lambda x: abs(x.x900_gag_max))
            all_ok = all(g.status == "OK" for g in gag_records)
            chk_str = "100.0%" if all_ok else "partial"
            lines.append(
                f"3. Coincident Max GAG Correlation: Across {len(gag_records)} evaluated channels, "
                f"peak X900 GAG load is {peak_gag.x900_gag_max:.4f} at {peak_gag.location} "
                f"(Mission Line {peak_gag.max_mission_line}, Endpoint {peak_gag.max_endpoint}). "
                f"Coincident non-range-paired (.nrang.out) endpoint reconciliation achieved "
                f"a delta check of {peak_gag.delta_check:.4f} ({chk_str} verification pass)."
            )
        return "\n".join(lines)

    def _call_ollama(self, prompt: str, params: GenParams) -> str | None:
        """Call local Ollama HTTP API on `127.0.0.1:11434/api/generate`."""
        payload = json.dumps(
            {
                "model": params.model_name,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": params.temperature,
                    "seed": params.seed,
                    "num_ctx": params.num_ctx,
                },
            }
        ).encode("utf-8")
        req = urllib.request.Request(
            f"{self.ollama_host}/api/generate",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=15.0) as resp:
                if resp.status == 200:
                    body = json.loads(resp.read().decode("utf-8"))
                    return body.get("response", "").strip()
        except Exception:
            return None
        return None
