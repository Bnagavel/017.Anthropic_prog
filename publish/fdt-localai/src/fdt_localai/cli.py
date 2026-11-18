"""Command-Line Interface for F&DT-LocalAI (`fdt` CLI)."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from fdt_localai.jobs.service import JobService
from fdt_localai.spectrum.pipeline import SpectrumPipelineOptions
from fdt_localai.spectrum.project_file_engine import audit_project_file
from fdt_localai.spectrum.rpt_to_elfo import convert_rpt_to_elfo


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="fdt",
        description="F&DT-LocalAI: Offline SPECTRUM Spectrum Pre/Post-Processing Engine (Release 1.0)",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # 1. `fdt run`
    p_run = sub.add_parser("run", help="Run a Spectrum pipeline or Task Recipe")
    p_run.add_argument(
        "target",
        help="Path to spectrum folder or recipe YAML (e.g. Spectrum/example or recipes/spectrum_postprocess.yaml)",
    )
    p_run.add_argument(
        "--inputs",
        nargs="*",
        default=[],
        help="Input folder or files when running a recipe YAML",
    )
    p_run.add_argument(
        "--base-name",
        default="SPECTRUM",
        help="Base Excel sheet name (max 19 chars, default: SPECTRUM)",
    )
    p_run.add_argument(
        "--static-values",
        action="store_true",
        help="Write static values instead of live Excel formulas (=IF, =SQRT)",
    )
    p_run.add_argument(
        "--ai-summary",
        action="store_true",
        help="Generate OEM-style comparison summary",
    )
    p_run.add_argument(
        "--output",
        default=None,
        help="Output .xlsx path",
    )

    # 2. `fdt audit`
    p_audit = sub.add_parser("audit", help="Audit a SPECTRUM project_file")
    p_audit.add_argument("project_file", help="Path to SPECTRUM project_file")

    # 3. `fdt rpt2elfo`
    p_rpt = sub.add_parser("rpt2elfo", help="Convert Patran .rpt file to SPECTRUM .elfo")
    p_rpt.add_argument("rpt_file", help="Path to Patran .rpt file")
    p_rpt.add_argument("--output", default=None, help="Output .elfo file path")
    p_rpt.add_argument("--template", default=None, help="Optional template .elfo for loadcase ordering")

    # 4. `fdt ui`
    p_ui = sub.add_parser("ui", help="Launch the local Excel-Form UI on 127.0.0.1:8501")
    p_ui.add_argument("--port", type=int, default=8501, help="Local port (default: 8501)")

    args = parser.parse_args(argv)

    if args.command == "run":
        target_p = Path(args.target)
        if target_p.suffix.lower() in (".yaml", ".yml"):
            folder_str = args.inputs[0] if args.inputs else "Spectrum/example"
            recipe_str = str(target_p)
        else:
            folder_str = str(target_p)
            recipe_str = "recipes/spectrum_postprocess.yaml"

        opts = SpectrumPipelineOptions(
            folder_path=folder_str,
            base_sheet_name=args.base_name,
            use_live_formulas=not args.static_values,
            generate_ai_summary=args.ai_summary,
            output_excel_path=args.output,
        )
        svc = JobService()
        out = svc.workflow.execute_spectrum_recipe(opts, recipe_path=recipe_str)
        print(f"[OK] Processed folder: {out.folder_path}")
        print(f"     .nrang.out files: {len(out.nrang_files)}")
        print(f"     Coincident GAG  : {len(out.gag_records)} locations")
        print(f"     C-Spec / fFI    : {len(out.cspec_results)} channels")
        print(f"     Elapsed time    : {out.elapsed_seconds:.3f} s")
        print(f"     Excel Workbook  : {out.excel_path}")
        print(f"     Run Manifest    : {out.manifest_yaml_path}")
        return 0

    if args.command == "audit":
        res = audit_project_file(args.project_file)
        res_clean = {k: v for k, v in res.items() if k != "model"}
        print(json.dumps(res_clean, indent=2))
        return 0 if res["error_count"] == 0 else 1

    if args.command == "rpt2elfo":
        rpt_p = Path(args.rpt_file)
        out_p = Path(args.output) if args.output else rpt_p.with_suffix(".elfo")
        deck = convert_rpt_to_elfo(
            rpt_p, output_elfo_path=out_p, template_elfo_path=args.template
        )
        print(
            f"[OK] Converted {rpt_p.name} -> {out_p} "
            f"({len(deck.rows)} element rows, {len(deck.loadcase_ids)} load cases)"
        )
        return 0

    if args.command == "ui":
        from fdt_localai.ui.app import serve_local_ui

        serve_local_ui(port=args.port)
        return 0

    return 0


if __name__ == "__main__":
    sys.exit(main())
