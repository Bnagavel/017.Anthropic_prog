"""Comprehensive unit, contract, golden-parity, and performance test suite for F&DT-LocalAI."""

from __future__ import annotations

import json
import time
from pathlib import Path

import openpyxl
import pytest

from fdt_localai.domain.calc_engine import (
    compute_margin_of_safety,
    compute_max_principal_and_angle,
    compute_resultant_load,
)
from fdt_localai.domain.checks import run_all_checks
from fdt_localai.domain.entity_resolver import EntityResolver
from fdt_localai.domain.models import Provenance, Quantity, Result, StructuralLocation
from fdt_localai.domain.units import DimensionalityError, convert_quantity, convert_value
from fdt_localai.llm.gateway import LLMGateway, NumberVerifier, StyleEngine
from fdt_localai.spectrum.coincident_gag import (
    custom_round_down_for_compare,
    extract_coincident_gag_folder,
)
from fdt_localai.spectrum.cspec_engine import (
    MaterialCSpecParams,
    evaluate_folder_cspec_ffi,
)
from fdt_localai.spectrum.nrang_engine import (
    build_x900_sequence,
    parse_nrang_file,
    parse_nrang_folder,
    parse_rang_file,
)
from fdt_localai.spectrum.pipeline import SpectrumPipelineOptions, run_spectrum_pipeline
from fdt_localai.spectrum.project_file_engine import (
    audit_project_file,
    generate_project_file,
    parse_project_file,
)
from fdt_localai.spectrum.rpt_to_elfo import (
    convert_rpt_to_elfo,
    parse_elfo_file,
)

REPO_ROOT = Path(__file__).resolve().parent.parent
example_DIR = REPO_ROOT / "Spectrum" / "example"
ELFO_SAMPLE_DIR = REPO_ROOT / "Spectrum" / "Input" / "Elfo" / "Excelvba_sample"
MAXP_SAMPLE_DIR = REPO_ROOT / "Spectrum" / "Misc" / "MaxP_Theta_Calc"
NRANG_PLOT_SAMPLE_DIR = REPO_ROOT / "Spectrum" / "Output" / "nrang_plot" / "sample"


# ============================================================================
# 1. Domain Layer Unit Tests (Units, Calc Engine, Checks, Entity Resolver)
# ============================================================================


@pytest.mark.unit
def test_unit_conversion_and_dimensionality() -> None:
    val_ksi = convert_value(68.94757293168361, "MPa", "ksi")
    assert pytest.approx(val_ksi, rel=1e-9) == 10.0

    prov = Provenance(
        file_sha256="abc1234",
        file_name="test.csv",
        locator="row 1",
        extractor="test",
    )
    q_mpa = Quantity(value=100.0, unit="MPa", provenance=prov)
    q_ksi = convert_quantity(q_mpa, "ksi")
    assert q_ksi.unit == "ksi"
    assert pytest.approx(q_ksi.value, rel=1e-6) == 14.5037738

    with pytest.raises(DimensionalityError):
        convert_value(100.0, "MPa", "mm")


@pytest.mark.unit
def test_calc_engine_primitives() -> None:
    prov = Provenance(
        file_sha256="abc1234",
        file_name="test.csv",
        locator="row 1",
        extractor="test",
    )
    applied = Quantity(value=100.0, unit="MPa", provenance=prov)
    allowable = Quantity(value=150.0, unit="MPa", provenance=prov)

    ms_qty = compute_margin_of_safety(
        applied_stress=applied, allowable_stress=allowable, scatter_factor=1.15
    )
    assert pytest.approx(ms_qty.value, rel=1e-9) == (150.0 / 115.0) - 1.0

    # Bearing resultant
    fbrg = compute_resultant_load(fx=3.0, fy=4.0)
    assert pytest.approx(fbrg, rel=1e-12) == 5.0

    # Principal stress 2D
    s_max, s_min, theta_deg = compute_max_principal_and_angle(sx=100.0, sy=0.0, sxy=0.0)
    assert pytest.approx(s_max, rel=1e-9) == 100.0
    assert pytest.approx(s_min, rel=1e-9) == 0.0
    assert pytest.approx(theta_deg, abs=1e-9) == 0.0


@pytest.mark.unit
def test_deterministic_checks_and_entity_resolver() -> None:
    prov = Provenance(
        file_sha256="abc1234",
        file_name="test.csv",
        locator="row 1",
        extractor="test",
    )
    res_neg = Result(
        location_id="LOC1",
        loadcase_id="LC1",
        kind="ms",
        label="Margin of Safety",
        quantity=Quantity(value=-0.05, unit="dimensionless", provenance=prov),
    )
    flags = run_all_checks([res_neg])
    assert any(f.rule_id == "negative_ms" for f in flags)

    loc = StructuralLocation(
        canonical_id="11.HM_LHmfs4",
        aliases=["11_HM_LHmfs4", "HM_LHmfs4.nrang.out"],
    )
    resolver = EntityResolver([loc])
    assert resolver.resolve("HM_LHmfs4.nrang.out") == "11.HM_LHmfs4"


# ============================================================================
# 2. LLM Guardrails (NumberVerifier & StyleEngine)
# ============================================================================


@pytest.mark.unit
def test_number_verifier_blocks_ungrounded_numbers() -> None:
    allowed = [108.13, -32.22, 1.1525, 0.7289, 25500.0, 1.0]

    valid_text = "Peak stress is 108.13 MPa with minimum -32.22 MPa and C-Spec 0.7289 over 25500 flights."
    ok, bad = NumberVerifier.verify_against_facts(valid_text, allowed)
    assert ok is True
    assert len(bad) == 0

    hallucinated_text = "Peak stress reached 999.42 MPa during flight 777."
    ok_bad, bad_nums = NumberVerifier.verify_against_facts(hallucinated_text, allowed)
    assert ok_bad is False
    assert 999.42 in bad_nums


@pytest.mark.unit
def test_style_engine_glossary_replacements() -> None:
    style = StyleEngine(REPO_ROOT / "config" / "glossary" / "oem_a.yaml")
    out = style.apply("The safety factor for X900 is verified.")
    assert "Scatter Factor" in out
    assert "X900" in out


# ============================================================================
# 3. Spectrum Core Modules (RPT -> ELFO, Project File, NRANG, Coincident GAG)
# ============================================================================


@pytest.mark.unit
def test_rpt_to_elfo_conversion(tmp_path: Path) -> None:
    rpt_file = ELFO_SAMPLE_DIR / "VS3_L2V01h_3.r1.d.rpt"
    ref_elfo = ELFO_SAMPLE_DIR / "VS3_L2V01h_3.r1.d.elfo"
    assert rpt_file.exists()
    assert ref_elfo.exists()

    out_elfo = tmp_path / "generated.elfo"
    gen_deck = convert_rpt_to_elfo(
        rpt_file, output_elfo_path=out_elfo, template_elfo_path=ref_elfo
    )
    ref_deck = parse_elfo_file(ref_elfo)

    assert len(gen_deck.rows) == len(ref_deck.rows)
    assert gen_deck.loadcase_ids == ref_deck.loadcase_ids
    for r_gen, r_ref in zip(gen_deck.rows[:30], ref_deck.rows[:30]):
        assert r_gen.elem_id == r_ref.elem_id
        assert r_gen.typ == r_ref.typ
        for lc in ref_deck.loadcase_ids[:10]:
            assert pytest.approx(r_gen.loads[lc], rel=1e-5, abs=1e-5) == r_ref.loads[lc]


@pytest.mark.unit
def test_project_file_parse_generate_and_audit(tmp_path: Path) -> None:
    proj_path = example_DIR / "project_file"
    pf = parse_project_file(proj_path)

    assert len(pf.stress_equations) == 10
    assert len(pf.output_mappings) == 10
    assert pf.output_mappings[0].output_prefix == "11.HM_LHmfs4"

    # Round-trip generation
    out_proj = tmp_path / "project_file_regen"
    out_proj.write_text(generate_project_file(pf), encoding="utf-8")
    pf_regen = parse_project_file(out_proj)
    assert len(pf_regen.stress_equations) == len(pf.stress_equations)
    assert [m.output_prefix for m in pf_regen.output_mappings] == [
        m.output_prefix for m in pf.output_mappings
    ]

    # Deterministic audit on example/project_file
    audit_res = audit_project_file(proj_path, base_dir=example_DIR)
    assert audit_res["error_count"] == 0


@pytest.mark.unit
def test_nrang_switch_and_x900_against_sample_workbook() -> None:
    nrang_files = parse_nrang_folder(NRANG_PLOT_SAMPLE_DIR)
    assert len(nrang_files) == 64

    x900_df = build_x900_sequence(nrang_files)
    assert len(x900_df) == 866

    # Verify against Nrang_spec_x900_plot_v1.xlsm reference sheets
    wb = openpyxl.load_workbook(
        NRANG_PLOT_SAMPLE_DIR.parent / "Nrang_spec_x900_plot_v1.xlsm", data_only=True
    )
    ws_x900 = wb["sample_nrangX900"]
    first_col_name = str(ws_x900.cell(1, 3).value)
    assert first_col_name in x900_df.columns
    for row_idx in range(10):
        ref_val = float(ws_x900.cell(row_idx + 2, 3).value)
        assert pytest.approx(float(x900_df[first_col_name].iloc[row_idx]), rel=1e-9) == ref_val


@pytest.mark.unit
def test_coincident_gag_max_principal_stress() -> None:
    assert MAXP_SAMPLE_DIR.exists()
    records = extract_coincident_gag_folder(MAXP_SAMPLE_DIR)
    assert len(records) >= 1
    rec = records[0]
    assert rec.mode == "MAXP_SX_SY_SXY"
    assert rec.location == "LOCA"
    assert rec.status == "OK"
    assert abs(rec.delta_check) < 0.05


# ============================================================================
# 4. Golden Dataset Numerical Parity Test (@pytest.mark.eval)
# ============================================================================


@pytest.mark.eval
@pytest.mark.skip(reason="Golden dataset removed from public release (derived from proprietary data)")
def test_golden_parity_example_cspec_and_ffi() -> None:
    golden_path = REPO_ROOT / "eval" / "golden" / "example_expected.json"
    assert golden_path.exists(), "Golden dataset JSON must exist"
    golden_data = json.loads(golden_path.read_text(encoding="utf-8"))["example"]

    params = MaterialCSpecParams.from_material_category("ALUMINUM", n=3.0)
    computed_list = evaluate_folder_cspec_ffi(example_DIR, params=params)

    assert len(computed_list) == len(golden_data) == 10

    for comp, gold in zip(computed_list, golden_data):
        assert comp.location == gold["location"]
        assert pytest.approx(comp.ffi, rel=1e-12) == gold["ffi"]
        assert pytest.approx(comp.cspec, rel=1e-12) == gold["cspec"]
        assert pytest.approx(comp.x900_max_over_ffi, rel=1e-12) == gold["x900_max_over_ffi"]
        assert pytest.approx(comp.x900_cycle_ffi, rel=1e-12) == gold["x900_cycle_ffi"]
        assert pytest.approx(comp.x900_cycle_ffi_ratio, rel=1e-12) == gold["x900_cycle_ffi_ratio"]
        assert pytest.approx(comp.x900_max, rel=1e-12) == gold["x900_max"]
        assert comp.x900_max_line == gold["x900_max_line"]
        assert pytest.approx(comp.x900_min, rel=1e-12) == gold["x900_min"]
        assert comp.x900_min_line == gold["x900_min_line"]


# ============================================================================
# 5. End-to-End Pipeline & Performance Benchmark (< 3.0 seconds)
# ============================================================================


@pytest.mark.perf
def test_full_pipeline_performance_under_3_seconds(tmp_path: Path) -> None:
    out_xlsx = tmp_path / "SPECTRUM_Perf_Test.xlsx"

    options = SpectrumPipelineOptions(
        folder_path=str(example_DIR),
        base_sheet_name="SPECTRUM",
        process_nrang=True,
        apply_s_switch=True,
        build_x900=True,
        extract_coincident_gag=True,
        compare_cspec_ffi=True,
        use_live_formulas=True,
        generate_ai_summary=True,
        audit_project_file_flag=True,
        output_excel_path=str(out_xlsx),
    )

    t0 = time.perf_counter()
    output = run_spectrum_pipeline(options)
    elapsed = time.perf_counter() - t0

    assert out_xlsx.exists()
    assert len(output.nrang_files) == 10
    assert len(output.cspec_results) == 10
    assert elapsed < 3.0, f"Expected < 3.0s for 10-channel pipeline, took {elapsed:.3f}s"

    # Verify required sheets exist
    wb = openpyxl.load_workbook(out_xlsx, data_only=False)
    expected_sheets = {
        "Control",
        "SPECTRUM_nrang",
        "SPECTRUM_nrangswitch",
        "SPECTRUM_nrangX900",
        "SPECTRUM_X900Plot",
        "Coincident_GAG",
        "CSPEC_fFI_Summary",
        "Audit_Trail",
        "Red_Flags",
        "Run_Manifest",
    }
    assert expected_sheets.issubset(set(wb.sheetnames))
