# Anthropic Fellows Application Pack (Draft)

> [!NOTE]
> Everything below comes from your CVs. Items in **[brackets]** need your input. Don't claim ML experience you don't have. Reviewers value honesty and evidence.

## 1. AI-focused CV (1 page)

**BASKARAN NAGAVEL** · Belfast, UK · baskaranpriyan@gmail.com · +44 7404 850176
UK Permanent Resident (full UK work authorisation) · GitHub: **[link once repos are public]**

**Profile**
Safety-critical systems engineer with 16+ years certifying aircraft structures to fatigue and damage-tolerance (F&DT) regulations. Experienced in building evidence for safety claims, validating analysis against full-scale test data, and setting inspection regimes for flaws that can't be fully prevented. Part-time postgraduate researcher at Queen's University Belfast. Moving into empirical AI safety research on evaluation, monitoring and control of frontier models.

**Assurance and technical highlights**
- Led F&DT certification analyses and reports accepted for **Transport Canada** approval on the A220-100/-300 wing and mid-fuselage.
- Improved inspection intervals (ALI) for A220 wing primary structure: balancing risk, detectability and maintenance burden.
- Correlated analysis with static and fatigue test results on critical airframe structures (FEA, NASGRO).
- Fatigue failure investigation and redesign of an industrial rubber-mixer rotor.
- Technical lead since 2023: mentoring engineers on certification; delivered classroom F&DT training. Best Project Execution Award (Tech Mahindra).

**Research**
Part-time PhD, Queen's University Belfast (2021–present): *Simulation Tools for the Design of Lightning Strike Protection Solutions*. Supervisor: **[confirm: Dr Scott Millen is named as reviewer in the thesis workspace; add full supervisory team]**. Differentiation report passed 2023; annual reviews 2024–2026; thesis drafting under way (Chapters 3–5 drafted). **[Add publications / conference output, or delete this note.]**
- Built coupled electric-thermal (Joule heating) ABAQUS models of lightning damage in composite laminates; showed that fibre-aligned meshing changes predicted damage area, and that high-fidelity runs are too slow (>20 days) for design studies.
- Designed a 27-run full-factorial DoE (plate length, width, top-ply angle) and automated model generation and post-processing with Python/MATLAB scripts.
- Built surrogate models to replace the FE runs. A quadratic regression predicts moderate damage area well (train R² 0.991, test R² 0.880). It failed on severe damage area, so I tested cubic and GAM models on 5 held-out non-grid geometries. GAM improved R² (0.82 combined) but gave non-physical step-wise predictions on sparse data. Gaussian Process and Support Vector regression are in progress.
- Skills transferable to AI safety work: evaluating models on held-out data, honest reporting of failure cases, and working with sparse, expensive-to-generate data.

**AI / software projects** (2025–2026; **[links once public]**)
- **F&DT-LocalAI**: offline LLM assistant (local Ollama, Gemma 2 / Qwen 2.5) that replaces 21 Excel VBA macros. It includes a **"zero-hallucination" number verifier** that checks every number in generated prose against a deterministic fact table, a deterministic fallback when the LLM is unavailable, a hybrid retrieval layer, and golden-file evaluations.
- **24x7 agent harness**: autonomous multi-model coding-agent loop with a **model router** (latency/success telemetry, automatic tier escalation) and a **human approval gate** over Discord (PROCEED / REFINE / SKIP).
- **AutoHex / HexPrep**: automated hex-meshing pipeline for aircraft fittings (STEP to mesh to validation); 63 commits, 59 test files, developed with agent assistance.
- **Beam foundation-model fine-tuning**: synthetic problem generation with analytical solutions and a validation framework that scores model output against closed-form solvers.
- **MCP servers/clients** for reading NASGRO input/output and plotting crack-growth data; PDF extraction toolset; task-logger desktop app.
- **PhD work (public)**: pseudocode and algorithm descriptions only (no code or data, as the work is unpublished): workflow, surrogate comparison and validation checks. Staged in publish/phd-lightning-surrogate/, to be pushed as a new repo with clean history, e.g. github.com/Bnagavel/phd-lightning-surrogate **[confirm name once pushed]**. The original Study_01 repo stays private (large input files, placeholder commits)

**Programming and training**
Python (NAFEMS *FEA for Python*; MITx *Computational Thinking using Python*), Excel VBA, TypeScript, in-house fatigue/fracture codes. LLM tooling: Ollama, Claude/Gemini CLIs, MCP. MATLAB (regression, GAM fitting). Python libraries used in the PhD code: NumPy, pandas, scikit-learn, pyDOE, Matplotlib, seaborn, Plotly, Shapely, Streamlit, plus the ABAQUS Python scripting API. **[Add any others you can be quizzed on.]**

**Experience**
- Morson Projects, Belfast: Stress, Fatigue & Damage Tolerance Engineer / Technical Lead (Oct 2015–present)
- Tech Mahindra (Bombardier ODC), Bangalore: Lead Engineer (May 2010–Sep 2015)
- National Aerospace Laboratories, Bangalore: Junior Engineer (Aug 2008–May 2010)

**Education**: B.E. Aeronautical Engineering, Madras Institute of Technology (2008). Baines Simmons: *Part 21 Subpart J – Understanding & Optimising your Design Organisation Approval (UK CAA DOA)* and the *CVE refresher* version.

## 2. Motivation statement (≈250 words)

I have spent 16 years answering one question: *how do we know this system is safe enough to fly?* On A220 and Global 7000 programmes I produced the fatigue and damage-tolerance evidence that regulators accept. That means assuming flaws will occur, predicting how they grow, checking analysis against physical tests, and choosing inspection intervals so problems are caught before they matter.

Frontier AI poses the same question with far less mature answers. Models can develop flaws that we can't fully see or prevent, and we depend on evaluations, monitoring and oversight to catch them in time. I believe the discipline of aviation assurance (safety cases, defence in depth, independent verification, test-correlated evidence) can help make AI evaluation and control more rigorous.

I'm building the empirical skills to contribute directly. **[Describe your project: what you built with open models or the Claude API, what you found, link to the write-up.]** My PhD at Queen's University Belfast builds surrogate models for expensive simulations. I've learned to validate on held-out cases and to report where a model fails, such as a quadratic fit that broke down on severe damage and a GAM that fit well but behaved unphysically. I work in Python daily.

I'm a UK permanent resident, able to commit full time for four months, and keen to work in **[London / remotely]**. I'd like to work on adversarial robustness and AI control, or on evaluations and scalable oversight, and I would welcome a full-time role in this field afterwards.

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
> **References:** the process includes a reference check. Line up 2 referees now, such as a Morson/Spirit manager and a QUB supervisor, and tell them in advance.
>
> **Employer data:** don't publish any Spirit/Bombardier/Airbus data or methods (e.g. BM7024). Use public NASGRO-style examples only.

## 5. Publishing your existing work (from `C:\Bask\00.AI`)

You already have more AI-relevant work than I assumed. The sorted list below shows what to make public.

| Project | Publish? | Why it matters to Anthropic | Before publishing |
|---|---|---|---|
| `013.LocalAI` | ✅ **Yes (flagship)** | Number verifier = hallucination control; local-only gateway; golden evals; deterministic fallback | Remove OEM-specific glossary, Golihat/Spectrum files and any real data |
| `016.24x7_Agent` | ✅ Yes (core of your proposal) | Autonomous agent with permission-skipping CLI flags, a router, and a human approval gate: directly relevant to **AI control** | **Delete `.env` and rotate the Discord token**; remove logs, attachments and `settings.local.json` |
| `006.BeamFoundationModel_Training` | ✅ Yes | LLM fine-tuning plus validation against ground truth | Drop `.venv`, checkpoints and large data |
| `010.AutoHex` | ⚠️ Optional | Shows engineering rigour (63 commits, 59 test files) | Check there is no employer geometry |
| `001.NASGRO_input_output`, `002.MCP_Client` | ⚠️ Optional | MCP tool-building | Remove NASGRO output from real programmes |
| `008.pdf_parser` | ❌ No | Built around Bombardier/Airbus methodology documents (AM7024) | Proprietary |
| `003`, `004`, `011`, `012`, `015`, `014` | Skip for this application | Not relevant to AI safety | n/a |

> [!CAUTION]
> Check for committed secrets and employer-confidential data in every repo before you make it public. Git history counts: use a fresh repo with a clean history if in doubt.

**Stronger research proposal:** your `016` harness already runs an agent with `--dangerously-skip-permissions` and a human approval gate. A natural project is to **measure how much human or monitor oversight is needed to catch unsafe agent actions** (the audit-interval idea in section 3), using your own harness and logs as the testbed. That gives you real code, real data and a clear link to AI Control.

## 6. Next steps I can help with
- Audit `013`, `016` and `006` for secrets and proprietary content and produce a clean copy ready to publish.
- Write the Python fatigue/crack-growth repo from scratch (public data only).
- Prototype the audit-interval experiment.
- Draft the "aircraft certification and AI safety" blog post.
