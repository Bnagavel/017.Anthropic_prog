# Anthropic Fellows Application Pack (Draft)

> [!NOTE]
> Everything below comes from your CVs. Items in **[brackets]** need your input. Don't claim ML experience you don't have. Reviewers value honesty and evidence.

## 0. Status (updated 21 Nov 2026)

| Item | State |
|---|---|
| 1-page CV (`cv/`) | Built and exported (`cv/Baskaran_Nagavel_AI_Safety_CV.docx` and `.pdf`, 1 page). Synced with section 1 below (generic private-project descriptions, no publications line, no supervisor name on CV) |
| Greenhouse form answers | Ready in `docs/greenhouse_application_answers.md` |
| Referees (for online form if asked) | **1.** Prof. Adrian Murphy (first PhD supervisor, QUB); **2.** Karthikeyan Gopalakrishnan (line manager, Morson Projects). Not listed on the CV |
| Repos in `publish/` | **Removed (employer-related risk):** `fdt-localai`, `agent-loop`. Kept: `beam-model-validation` (checked; synthetic data, `implementation_guide.md` scrubbed), `phd-lightning-surrogate` (pseudocode only, **private**; Prof. Adrian Murphy's approval needed before outside sharing) |
| `ai-control-project/` | Empirical AI Control experiment complete (separation 2.202, p_ok 0.600). Scrubbed of local paths and employer doc IDs; runs from a frozen snapshot with no private repo. Added to CV and motivation statement. Keep **private** and share on request |
| Still to do | Open `cv/Baskaran_Nagavel_AI_Safety_CV.pdf` to check layout, notify referees and collect their email/phone, confirm A220/Transport Canada CV wording, create private GitHub repos (`ai-control-project`, etc.) if sharing on request, submit |

> [!WARNING]
> This top-level folder holds personal CVs, certificates and the full chat log. Sync it between machines only through a **private** GitHub repo. Create each repo you share as its own new repo with clean history (private for now; give access to an interviewer only if requested). `fdt-localai` and `agent-loop` were removed from this project.

## 1. AI-focused CV (1 page)

> Exported to `cv/Baskaran_Nagavel_AI_Safety_CV.docx` and `cv/Baskaran_Nagavel_AI_Safety_CV.pdf` (from `cv/cv_source.html`).

**BASKARAN NAGAVEL** · Belfast, UK · baskaranpriyan@gmail.com · +44 7404 850176
UK Permanent Resident (full UK work authorisation)

**Profile**
Aerospace structural engineer with 17+ years of experience, certifying aircraft structures under fatigue and damage-tolerance (F&DT) regulations — building test-correlated evidence and inspection regimes for flaws that cannot be fully prevented. Part-time PhD researcher (Queen's University Belfast) building surrogate models for expensive simulations. Independently exploring AI tools and empirical AI safety & control out of personal interest, driven by the parallels to aviation assurance and the oversight needed to evaluate AI for regulated engineering.

**Research**
**Part-time PhD, Queen's University Belfast (2021–present):** *Simulation Tools for the Design of Lightning Strike Protection Solutions.* Thesis drafting under way.
- Built coupled electric-thermal (Joule heating) ABAQUS models of lightning damage in composite laminates. Showed that fibre-aligned meshing changes predicted damage area, and that high-fidelity runs (>20 days) are too slow for design studies.
- Designed a 27-run full-factorial experiment (plate length, width, top-ply angle); automated model generation and post-processing in Python and MATLAB.
- Built surrogate models to replace the FE runs. Quadratic regression predicts moderate damage area well (train R² 0.991, test R² 0.880) but failed on severe damage. Tested cubic and GAM models on 5 held-out non-grid geometries; GAM improved R² (0.82) but gave non-physical step-wise predictions on sparse data. Reported both outcomes. Gaussian-process and support-vector regression in progress.

**Independent AI & AI safety projects (self-directed)**
- **AI Control experiment (2026).** Reproduced the trusted-monitoring safety calculation from Greenblatt et al. (2023), then applied it to 30 code diffs: 15 real commits from my own meshing codebase and 15 hand-written sabotage diffs, scored by a rule-based monitor. Measured separation 2.2 and 60% exploit viability. At a 5% audit budget the Gaussian model predicted 80% safety against 92% measured (n=15, wide uncertainty). Limitation stated in the write-up: the monitor rules were written knowing the attacks, so this checks the method, not monitor quality. Next step: local-LLM monitor (Ollama).
- **Autonomous coding loop with human approval gate (2025–26).** Built a multi-model agent loop with automatic model routing and a human approve/refine/skip checkpoint. Identified specification gaming (hard-coded dimensions to pass mesh tests) and added rules against it.
- **Local-LLM assistant with deterministic output checking (2025–26).** Offline assistant (Ollama, Gemma 2 / Qwen 2.5) that checks every number in generated text against a deterministic table, with a non-LLM fallback and golden-file tests.
- **Model validation against ground truth.** Synthetic beam problems with closed-form solutions used to score fine-tuned model output.

**Aerospace structural & certification experience**
- Morson Projects, Belfast — **Stress, Fatigue & Damage Tolerance Engineer / Technical Lead** (Oct 2015–present). Technical lead since 2023: mentoring engineers on certification. Led F&DT certification analyses and reports accepted for Transport Canada approval (A220-100/-300 wing and mid-fuselage). Improved inspection intervals (ALI) for wing primary structure, balancing risk, detectability and maintenance burden. Correlated analysis with static and fatigue test results (FEA, NASGRO).
- Tech Mahindra (Bombardier ODC), Bangalore — **Lead Engineer** (May 2010–Sep 2015). Static and F&DT analysis of fuselage structures; full-scale test correlation; delivered classroom F&DT training. Best Project Execution Award.
- National Aerospace Laboratories, Bangalore — **Junior Engineer** (Aug 2008–May 2010). Nacelle structural design.

**Skills and training**
**Python:** NumPy, pandas, scikit-learn, Matplotlib, seaborn, Plotly, pyDOE, Shapely, Streamlit, pytest, ABAQUS scripting API. Also MATLAB, Excel VBA, TypeScript. **LLM tooling:** Ollama, Claude and Gemini CLIs, MCP servers. **Training:** NAFEMS *FEA for Python*; MITx *Computational Thinking using Python*; Baines Simmons *Part 21 Subpart J – Understanding & Optimising your Design Organisation Approval (UK CAA DOA)* and CVE refresher.

**Education**
B.E. Aeronautical Engineering, Madras Institute of Technology (2008). Postgraduate research, Queen's University Belfast (2021–present).

*(Ready-to-paste Greenhouse form answers are in `docs/greenhouse_application_answers.md`.)*

## 2. Motivation statement

I have spent 17+ years as an aerospace structural engineer answering one question: *how do we know this structure is safe enough to fly?* Certifying aircraft structures under fatigue and damage-tolerance (F&DT) regulations means assuming flaws will occur, predicting how they grow, correlating analysis against physical tests, and choosing inspection intervals so problems are caught before they compromise safety.

Seeing how significant AI is becoming across aerospace engineering and my part-time PhD research, I started experimenting hands-on with local LLMs and agentic tools out of personal interest. As I explored practical usage—and thought through how to discuss and justify introducing AI tools responsibly with engineering management in a heavily regulated industry—it became clear that capability alone is not enough. Explaining and governing these systems required concrete **AI safety and control** knowledge, and my interest naturally deepened into AI safety because it follows the same underlying logic as aircraft damage-tolerance assurance: monitoring imperfect systems, bounding silent failures, and designing oversight regimes that hold under worst-case assumptions.

Alongside my day job, I began building empirical skills independently. To understand the field practically, I reproduced the trusted-monitoring safety calculation from Greenblatt et al.'s *AI Control* paper and tested it on 30 code diffs from my own meshing codebase (15 real commits and 15 hand-written sabotage diffs) scored by a rule-based monitor. The Gaussian model predicted 80.4% safety at a 5% audit budget against 91.7% measured, though with only 15 attacks and rules tuned knowing them, I treat this strictly as a method check rather than a benchmark—and it taught me how safety hinges on the single subtle attack (`atk_12`) that slips below the threshold. Separately, my QUB PhD builds surrogate models for expensive finite-element simulations, where I validate rigorously on held-out cases and report model breakdowns honestly.

I hold UK Permanent Residency (Indefinite Leave to Remain), can commit full time for four months, and am open to working either in London or remotely within the UK. I would like to contribute to adversarial robustness and AI control, or scalable oversight, and would welcome a full-time role in this field afterwards.

## 3. Research proposal sketch

**Title:** *Audit-interval design for AI monitoring: borrowing damage-tolerance logic for agent oversight*

| Element | Plan |
|---|---|
| Question | Given a monitor with imperfect detection, how should audit frequency and strength scale with the rate and growth of unsafe agent behaviour? |
| Analogy | Crack initiation, growth and detection: probability of detection, inspection interval, residual strength |
| Method | Run an open-weights model in an agentic task with injected unsafe behaviours. Vary monitor strength and audit rate. Measure the unsafe-action rate that gets through, and the cost of auditing |
| Output | A simple model plus empirical curves, a short paper or blog post, and open code |
| Fit | Matches the AI Control and Adversarial Robustness workstream. Uses open models, which is what Fellows primarily use |

**Backup idea:** a safety-case template for AI deployment adapted from aviation certification structure, tested against public evaluation results.

## 4. Six-week plan

| Week | Goal |
|---|---|
| 1 | Set up GitHub. Publish a cleaned Python fatigue / crack-growth tool (no employer data). Start the BlueDot *AI Safety Fundamentals* course |
| 2 | Read Anthropic's Alignment Science blog and the AI Control papers. Pick the project; write a 1-page plan |
| 3–4 | Build the experiment with an open model or the Claude API; log results |
| 5 | Write it up (blog or arXiv-style). Publish code |
| 6 | Finalise CV and statement, line up referees, and submit |

> [!IMPORTANT]
> **References (confirmed for online form if asked — not on CV):**
> 1. **Prof. Adrian Murphy** — First PhD Supervisor, Queen's University Belfast (School of Mechanical & Aerospace Engineering)
> 2. **Karthikeyan Gopalakrishnan** — Line Manager, Morson Projects
> *(Give both a heads-up and add their email/phone before submitting.)*
>
> **Employer data:** don't publish any Spirit/Bombardier/Airbus data or methods (e.g. BM7024). Use public NASGRO-style examples only.
> **PhD sharing:** get **Prof. Adrian Murphy's** approval before sharing `publish/phd-lightning-surrogate/` outside. (Dr Scott Millen was listed only as an internal thesis reviewer.)

## 5. Publishing your existing work (from `C:\Bask\00.AI`)

You already have more AI-relevant work than I assumed. The sorted list below shows what to make public.

| Project | Publish? | Why it matters to Anthropic | Before publishing |
|---|---|---|---|
| `013.LocalAI` | ❌ **Removed (employer-related risk)** | Number verifier = hallucination control; local-only gateway; golden evals; deterministic fallback | Remove OEM-specific glossary, Golihat/Spectrum files and any real data |
| `016.24x7_Agent` | ❌ **Removed (employer-related risk)** | Autonomous agent with permission-skipping CLI flags, a router, and a human approval gate: directly relevant to **AI control** | **Delete `.env` and rotate the Discord token**; remove logs, attachments and `settings.local.json` |
| `006.BeamFoundationModel_Training` | ✅ Yes | LLM fine-tuning plus validation against ground truth | Drop `.venv`, checkpoints and large data |
| `010.AutoHex` | ⚠️ Optional | Shows engineering rigour (63 commits, 59 test files) | Check there is no employer geometry |
| `001.NASGRO_input_output`, `002.MCP_Client` | ⚠️ Optional | MCP tool-building | Remove NASGRO output from real programmes |
| `008.pdf_parser` | ❌ No | Built around Bombardier/Airbus methodology documents (AM7024) | Proprietary |
| `003`, `004`, `011`, `012`, `015`, `014` | Skip for this application | Not relevant to AI safety | n/a |
| PhD code (`Study_01`) | ⚠️ Pseudocode only, private for now | Shows research method without releasing unpublished code | Done: see `publish/phd-lightning-surrogate/`. Keep `Study_01` private |

> [!CAUTION]
> Check for committed secrets and employer-confidential data in every repo before you make it public. Git history counts: use a fresh repo with a clean history if in doubt.

**Stronger research proposal:** your `016` harness already runs an agent with `--dangerously-skip-permissions` and a human approval gate. A natural project is to **measure how much human or monitor oversight is needed to catch unsafe agent actions** (the audit-interval idea in section 3), using your own harness and logs as the testbed. That gives you real code, real data and a clear link to AI Control.

## 6. Next steps I can help with
- Audit `013`, `016` and `006` for secrets and proprietary content and produce a clean copy ready to publish.
- Write the Python fatigue/crack-growth repo from scratch (public data only).
- Prototype the audit-interval experiment.
- Draft the "aircraft certification and AI safety" blog post.
