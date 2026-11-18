# F&DT-LocalAI

> **Offline, privacy-preserving AI assistant for Metallic Fatigue & Damage Tolerance engineering**

[![Platform: Windows 11](https://img.shields.io/badge/Platform-Windows_11_x64-blue.svg)](#)
[![Python: 3.11+](https://img.shields.io/badge/Python-3.11+-green.svg)](#)
[![Runtime: Ollama / llama.cpp](https://img.shields.io/badge/Runtime-Ollama%20%2F%20llama.cpp-orange.svg)](#)
[![Security: Air-Gapped](https://img.shields.io/badge/Security-Air--Gapped%20Local-red.svg)](#)

| Document | Purpose |
| :--- | :--- |
| [PROJECT_PLAN.md](PROJECT_PLAN.md) | Scope, use cases, success criteria, roadmap, risks, open decisions |
| [ARCHITECTURE.md](ARCHITECTURE.md) | Software architecture: review findings, layers, data model, workflow, LLM usage, security, quality |

---

## 1. Release 1.0: The SPECTRUM Spectrum Engine

**F&DT-LocalAI (Release 1.0)** is an offline, high-speed engineering application designed to replace 21 fragile Excel VBA macros used in SPECTRUM spectrum pre-processing and post-processing. It features an **ultra-simple Excel-form-style interface** (no confusing or fancy web dashboards) that allows engineers to select folders, check processing options, preview tables, and export formatted multi-tab Excel workbooks with live formulas.

```
+----------------------------------------------------------------------------------------------------+
|                                    RELEASE 1.0 WORKFLOW PIPELINE                                   |
+----------------------------------------------------------------------------------------------------+
|  [Pre-Processing]   Patran .rpt -> .elfo converter | 'project_file' builder & AI syntax audit      |
|  [SPECTRUM Exec]     SPECTRUM.exe executed externally by engineer                                    |
|  [Post-Processing]  .nrang.out vector parser | 'S' switch logic | X900 flight-point unrolling       |
|  [Analysis]         Coincident Max GAG extractor (FBRG <-> FX, FY) | C-Spec / fFI severity calc    |
|  [Excel Output]     Control, _nrang, _nrangswitch, _nrangX900, Coincident_GAG (Formulas or Values) |
+----------------------------------------------------------------------------------------------------+
```

### Key Principles
- **Clean & Simple Excel-Form UI:** Designed like a classic Excel UserForm with folder picker, task checkboxes, run button, and download link. No complex or intimidating dashboards.
- **Numbers Never Come from the AI:** Parsers and analytical math engines process all numbers deterministically.
- **Live Excel Formulas or Static Values:** User toggle outputs active `=IF(...)` and `=SQRT(...)` formulas or static numbers.
- **Offline & Air-Gapped:** 100% local execution on `127.0.0.1` with zero network egress.
- **Local AI Audit (Gemma 2 2B):** Runs strictly on-demand to check `project_file` syntax or draft OEM report comparison text.

---

## 2. Supported Inputs (v1)

| Category | Formats | Notes |
| :--- | :--- | :--- |
| Nastran | `.bdf`, `.dat`, `.op2`, `.f06` | Parsed with pyNastran; OP2 preferred |
| Abaqus | `.inp`, `.dat`, `.rpt` | `.odb` out of scope |
| Stress spectra | `.txt`, `.csv`, `.spc`, in-house | Rainflow, exceedance and R-ratio computed deterministically |
| Crack growth | NASGRO / AFGROW outputs | One plugin per format/version |
| Reports | Digital (text-layer) PDF, any length | Scanned PDFs detected and rejected (no OCR) |
| Calc sheets | `.xlsx`, `.xlsm`, `.xls` | Macros never executed; stale formulas flagged |

---

## 3. Hardware & Models

Target laptop: Intel Core i7-1360P (12C/16T) · 64 GB RAM · NVIDIA RTX A500 (4 GB VRAM).

| Tier | Default model | Placement | Used for |
| :--- | :--- | :--- | :--- |
| `fast` | **Gemma-2-2B-Instruct** (Q4_K_M) | 100% GPU (<1.9 GB VRAM, 8k ctx) | Header mapping proposals, entity resolution, quick Q&A |
| `reasoning` | **Qwen2.5-7B-Instruct** (Q4_K_M) | Hybrid GPU/RAM (~3.45 GB VRAM) | Section narratives, multi-source synthesis, audit |
| `embed` | nomic-embed-text / bge-small-en-v1.5 | CPU (16 threads) | Chunk retrieval & document vector search |

Tiers are confirmed by the Phase 0 benchmark and configured in `config/models.yaml`. See [ARCHITECTURE.md §9](ARCHITECTURE.md) for the sizing math.

---

## 4. Repository Layout

```
013.LocalAI/
|-- README.md / PROJECT_PLAN.md / ARCHITECTURE.md
|-- launch.ps1              # start/stop UI, worker, Ollama
|-- pyproject.toml
|-- config/                 # app.yaml, models.yaml, glossary/
|-- recipes/                # Task Recipes (versioned YAML)
|-- blueprints/             # report-format mappings
|-- prompts/                # versioned prompt templates
|-- templates/excel|word/   # house-style output templates
|-- src/fdt_localai/        # domain, ingestion, retrieval, llm, workflow, render, store, jobs, ui, cli
|-- tests/                  # unit, contract, integration, eval, perf
|-- eval/golden/            # sanitised golden datasets
`-- workspace/              # per-project data (git-ignored)
```

---

## 5. Quickstart (once implemented)

```powershell
# 1. Offline install (wheelhouse prepared on a connected machine and transferred)
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install --no-index --find-links .\wheelhouse -r requirements.txt

# 2. Models: pre-staged GGUF files are verified against config/models.yaml, then registered with Ollama
$env:OLLAMA_HOST = "127.0.0.1"
ollama pull gemma2:2b-instruct-q4_K_M        # on a connected machine, or import from the staged files
ollama pull qwen2.5:7b-instruct-q4_K_M

# 3. Launch UI + worker + Ollama (all bound to 127.0.0.1)
.\launch.ps1 start

# 4. Or run a recipe from the CLI
fdt run recipes\fatigue_ms_summary.yaml --inputs wing_rib4.op2 rib4_calc.xlsx report_123.pdf
```

---

## 6. Audit & Traceability

Every output workbook contains:
- **Audit_Trail** sheet: each value with its source file, SHA-256 and locator (`p.142 L18`, `Sheet1!D24`, `OP2 SUBCASE 3 EID 10423`)
- **Red_Flags** sheet: negative MS, low scatter factor, unit issues, missing provenance, unresolved entities
- **Run_Manifest** sheet: recipe version, code version, input hashes, model SHA-256, prompt versions, seed/temperature, reviewer and approval timestamp
