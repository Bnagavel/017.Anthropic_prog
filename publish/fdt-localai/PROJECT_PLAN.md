# F&DT-LocalAI: Project Plan

**Document Version:** 2.2.0  
**Target Platform:** Windows 11 x64 · Intel Core i7-1360P (12C/16T) · 64 GB RAM · NVIDIA RTX A500 Laptop GPU (4 GB VRAM)  
**Operating Mode:** 100% offline / air-gapped, local execution only  
**Primary Focus (Release 1.0):** SPECTRUM Spectrum Pre/Post-Processing Engine (Complete VBA Replacement & AI Audit)  
**UI Philosophy:** Clean, utilitarian, "Excel-form-style" interface (simple inputs, action buttons, table preview, one-click Excel download)  
**Companion documents:** [ARCHITECTURE.md](ARCHITECTURE.md) (software design) · [README.md](README.md) (overview, quickstart)

---

## 1. Release 1.0 Executive Scope: The Spectrum Engine

### 1.1 Objective
Release 1.0 replaces fragile, slow Excel VBA macros (from the `Spectrum` folder) with a high-performance, 100% offline local Python + AI application. It automates SPECTRUM spectrum input preparation, output sequence transformation, coincident GAG load extraction, and C-Spec fatigue severity comparison, outputting formatted Excel workbooks (`.xlsx`) with optional live formulas.

```
+----------------------------------------------------------------------------------------------------+
|                                    RELEASE 1.0 PIPELINE OVERVIEW                                   |
+----------------------------------------------------------------------------------------------------+
|                                                                                                    |
|  [PRE-PROCESSING: SPECTRUM Input Setup]                                                             |
|  1. Patran .rpt -> .elfo converter: Translates FE load printouts into standard .elfo format.       |
|  2. 'project_file' Parser & Validator:                                                             |
|     - Parses Project Name, Target Directory, Load URLs (.elfo, .ldp, .def).                       |
|     - Parses & maps Stress Transfer Equations (e.g. Q01 = -1* EF(11,F)).                           |
|     - Parses & links Output File Mappings (e.g. Q01 : 11.HM_LHmfs4).                              |
|     - AI Audit (on demand): Checks equation syntax, load indices, and parameter sanity.            |
|                                                                                                    |
|  [SPECTRUM EXECUTION: Handled Externally by Engineer]                                               |
|                                                                                                    |
|  [POST-PROCESSING: Spectrum Extraction & Analysis]                                                 |
|  3. Sequence Extraction & Transformation (replaces Extract_nrang_out_all.bas):                     |
|     - High-speed vector parsing of 10-column space-delimited .nrang.out files.                     |
|     - Switch Logic: Swaps Stress 1 & 2 when switch column suffix has 'S'.                          |
|     - X900 Unrolling: Filters Occurrences >= 1 into sequential continuous flight points.           |
|  4. Coincident Max GAG Extraction (replaces Extract_X900_GAG_nrang.bas):                          |
|     - Correlates peak GAG in *_FBRG.rang.out with simultaneous FX.nrang.out and FY.nrang.out.      |
|     - Verifies resultant vector sanity: SQRT(FX^2 + FY^2) ~= FBRG.                                 |
|  5. C-Spec & fFI Severity Comparison (replaces Calc_CSpec_Tool.xlsm):                              |
|     - Computes equivalent fatigue stress ($S_{eq}$) and severity ratio ($f_{FI}$) deltas.          |
|  6. Simple Verification Plotting (replaces Spectrum_Plot_Tool.bas):                                |
|     - Lightweight, responsive XY scatter time-history plot with channel toggles.                  |
|                                                                                                    |
|  [OUTPUT GENERATION]                                                                               |
|  7. Formatted Multi-Tab Excel Workbook (.xlsx):                                                    |
|     - Generates Control, _nrang, _nrangswitch, _nrangX900, Coincident_GAG sheets.                  |
|     - User toggle: Output with LIVE EXCEL FORMULAS (=IF, =SQRT) or STATIC VALUES.                  |
|     - Optional on-demand OEM comparison text summary written by Gemma 2 2B.                        |
+----------------------------------------------------------------------------------------------------+
```

---

## 2. User Interface Philosophy: "Simple Excel Form"

To ensure stress engineers feel immediately comfortable without being overwhelmed by complicated web designs:
- **No fancy, complex dashboards:** The UI is designed like a classic **Excel UserForm / Control Panel**.
- **Minimalist Form Layout:**
  1. **Folder Selection:** Select directory containing spectrum files.
  2. **Task Checkboxes:** Check desired tasks (e.g., `[X] Extract Coincident GAG`, `[X] Build X900`).
  3. **Formula Toggle:** `[X] Include Live Excel Formulas (=IF, =SQRT)`.
  4. **Run Button:** A clear, prominent `[ Run Processing ]` button.
  5. **Table Preview & Download:** A clean spreadsheet-like preview grid with a `[ Download Excel (.xlsx) ]` button.

```
+----------------------------------------------------------------------------------------------------+
| F&DT Spectrum Assistant (Release 1.0)                                           [Offline Mode: OK] |
+----------------------------------------------------------------------------------------------------+
|                                                                                                    |
|  1. Select Spectrum Folder:                                                                        |
|     [ <WORKSPACE>/013.LocalAI\Spectrum\example           ] [ Browse Folder ]             |
|                                                                                                    |
|  2. Select Processing Options:                                                                     |
|     [X] Process .nrang.out (Extract Stress 1, Stress 2, Occurrences)                                |
|     [X] Apply 'S' Switch Logic (Swap Stress 1 and Stress 2)                                        |
|     [X] Build X900 Flight-Point Sequence (Occurrences >= 1)                                        |
|     [X] Extract Coincident Max GAG Loads (Correlate FBRG with FX and FY)                            |
|     [X] Compare Spectrum Severity (C-Spec / fFI)                                                   |
|                                                                                                    |
|  3. Excel Output Setting:                                                                          |
|     (o) Live Excel Formulas (=IF, =SQRT)      ( ) Static Values (Fastest)                         |
|                                                                                                    |
|  4. Optional AI Report Summary:                                                                    |
|     [ ] Generate OEM-Style Comparison Summary (Drafted by local Gemma 2 2B)                        |
|                                                                                                    |
|  ------------------------------------------------------------------------------------------------  |
|  [ RUN PROCESSING ]                                                                                |
|  ------------------------------------------------------------------------------------------------  |
|                                                                                                    |
|  Results Preview (Coincident Max GAG Summary):                                                     |
|  +-----------------------------------------------------------------------------------------------+ |
|  | Location    | Max FBRG (kN) | Mission Line | Endpoint | Coincident FX | Coincident FY | Check  | |
|  | HM_LHmfs1   | 42.82         | 904_2        | Touchdown| -12.41        | +8.10         | OK     | |
|  | HM_LHmfs2   | 38.15         | 904_2        | Touchdown| -10.12        | +7.45         | OK     | |
|  +-----------------------------------------------------------------------------------------------+ |
|                                                                                                    |
|  [ DOWNLOAD EXCEL WORKBOOK (.XLSX) ]                                                               |
+----------------------------------------------------------------------------------------------------+
```

---

## 3. Scope Inventory: VBA Macro Migration Matrix

| Existing VBA File in `Spectrum/` | Core VBA Functionality | Release 1.0 Python + AI Replacement |
| :--- | :--- | :--- |
| `Extract_nrang_out_all.bas` | Space-delimited text-to-columns parsing of `.nrang.out` across folders via clipboard | Fast in-memory vector parser (`numpy`/`polars`); parses 100+ files in < 1 second. |
| `Nrang_spec_x900_plot_v1.xlsm` & `Spectrum_Plot_Tool.bas` | Switch 'S' logic, X900 unrolling, and 64-channel XY scatter plotting | Generates `_nrangswitch` and `_nrangX900` tabs with live `=IF(...)` formulas; lightweight interactive line plot. |
| `Extract_X900_GAG_nrang.bas` & `Brg_Loads_nrang_extract_all.xlsm` | Correlates `_FBRG.rang.out` with `_FX` and `_FY` to find coincident loads at max GAG | High-speed relational join matches line IDs at peak GAG; writes `=SQRT(FX^2 + FY^2)` validation formula. |
| `Patran_Rpt_to_ELFO_format_converter_v1.02_p19_2.xlsm` | Converts Patran FE load output `.rpt` into standard `.elfo` columns | Deterministic token parser formats loads into `.elfo` / `.endl` decks. |
| `TrAll_LugC_Nasgro_ProjectFile_v2.xlsm` | Formats `project_file` headers, paths, parameters, and stress equations | Declarative `project_file` generator with AI syntax & transfer function auditing. |
| `Calc_CSpec_Tool_v1.0.xlsm` & `G7000_ffi_cspec...xlsm` | Calculates C-Spec damage indices and $f_{FI}$ severity comparison ratios | Exact analytical damage summation formula; optional AI-drafted comparison text. |

---

## 4. Hardware Sizing & Local AI Role

### 4.1 Hardware Fit
- **Processor:** Intel Core i7-1360P (16 threads handle multi-file spectrum parsing concurrently).
- **RAM:** 64.0 GB DDR5 (holds millions of spectrum data points in memory with zero disk paging).
- **GPU:** NVIDIA RTX A500 Laptop GPU (4.0 GB VRAM).

### 4.2 Local AI Model Allocation
* **Primary Model:** **Google Gemma 2 2B Instruct (Q4_K_M)**
  * **Memory:** Requires only **~1.6 GB** for weights, **~0.23 GB** for KV cache (q8).
  * **VRAM Footprint:** **~1.85 GB total** (< 50% of RTX A500 VRAM, zero OOM risk).
  * **Inference Speed:** **~35–48 tokens/sec** on GPU.
* **AI Model Responsibilities (Strictly On-Demand):**
  1. **Pre-Run `project_file` Audit:** Checks transfer function syntax (`Q01 = -1* EF(11,F)`), verifies that referenced `.elfo` load indices exist, and flags unit inconsistencies before running SPECTRUM.
  2. **Report Summary Writer (When Checked by User):** Takes the deterministic C-Spec / GAG delta table and generates an OEM-style comparison paragraph for engineering reports.
  3. **Zero-Hallucination Policy:** The AI model **never** calculates or alters numerical data. All numbers originate from Python parsers.

---

## 5. Implementation Roadmap (Release 1.0 Sprints)

Effort estimate: **4 to 5 Weeks** for a focused, robust delivery.

### Sprint 1: Pre-Processing & Parser Core (Weeks 1–2)
- [ ] Build Patran `.rpt` to `.elfo` load converter (`rpt_to_elfo.py`).
- [ ] Build `project_file` parser and generator with transfer equation mapping (`project_file_engine.py`).
- [ ] Build ultra-fast `.nrang.out` and `.rang.out` vector parsers with 'S' switch logic (`nrang_engine.py`).
- [ ] Unit test on `<WORKSPACE>/013.LocalAI\Spectrum\example` dataset.

### Sprint 2: Coincident GAG, C-Spec & Excel Formatter (Week 3)
- [ ] Build Coincident GAG extraction engine correlating `_FBRG`, `_FX`, and `_FY` at peak X900 point (`coincident_gag.py`).
- [ ] Build C-Spec & $f_{FI}$ fatigue damage severity calculation engine (`cspec_engine.py`).
- [ ] Build Excel report generator (`excel_writer.py`) supporting both **Live Formulas Mode** (`=IF(...)`, `=SQRT(...)`) and **Static Values Mode**.

### Sprint 3: Simple Excel-Style UI & Local AI Integration (Week 4)
- [ ] Build minimalist Streamlit interface styled like a clean Excel userform (`ui_app.py`).
- [ ] Integrate local Gemma 2 2B via Ollama for on-demand `project_file` audit and comparison summaries.
- [ ] Add simple verification line chart for time-history inspection.

### Sprint 4: Verification, Benchmarking & Packaging (Week 5)
- [ ] Benchmark 100% numerical match against existing VBA macro workbooks (`Nrang_spec_x900_plot_v1.xlsm`, `Extract_X900_GAG_nrang.bas`).
- [ ] Air-gap verification test (100% offline in Windows Airplane Mode).
- [ ] Package one-click Windows launcher (`launch_spectrum_tool.bat`).

---

## 6. Success Criteria for Release 1.0

1. **Numerical Parity:** 100% exact numerical match with legacy VBA outputs across all channels in `example`.
2. **Performance:** Processing 10 channels of `.nrang.out` (50,000+ points) and generating the multi-tab Excel workbook takes **< 3 seconds** (compared to 30–60 seconds in VBA).
3. **Usability:** Non-programmer engineers can perform the entire workflow via simple folder selection and button clicks.
4. **Formula Fidelity:** Excel workbooks open cleanly in Microsoft Excel with active, working formulas and zero `#SPILL!` or `#REF!` errors.
5. **Security:** 0 bytes of external network communication.
