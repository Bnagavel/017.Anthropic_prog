# Session Handoff — Anthropic Fellows Program & AI Control Study

Use this file to resume on another machine (or point a fresh AI assistant at `docs/HANDOFF_NEXT_MACHINE.md`). Last updated 21 Nov 2026.

> **PRIVACY:** This top-level folder holds personal CVs/cover letters (contact details, passport number in `Baskaran_Nagavel_Resume_2025.docx`), certificates and the full private chat log. Sync it **only through a private GitHub repo**. Every project repo you share is created separately from its own folder, with fresh history, and stays private unless an interviewer asks.

---

## 1. Inventory

### A. CV & Application Materials (`cv/`, `docs/`)
- `cv/Baskaran_Nagavel_AI_Safety_CV.docx` & `cv/Baskaran_Nagavel_AI_Safety_CV.pdf` — 1-page AI-focused CV built from `cv/cv_source.html` via `cv/build_cv.ps1` (Word COM export).
- `docs/greenhouse_application_answers.md` — Copy-paste answers for Greenhouse ([AI Safety & Security `5183044008`](https://job-boards.greenhouse.io/anthropic/jobs/5183044008)), including confirmed referees (**Prof. Adrian Murphy** and **Karthikeyan Gopalakrishnan**).
- `docs/anthropic_fellowship_recommendation.md` — Track analysis. Primary: `5183044008`; optional secondary: `5183053008`.
- `docs/anthropic_application_pack.md` — Master application pack synced with the final 1-page CV and confirmed choices.
- `docs/ai_control_stats_presentation.md` — Slide-deck walkthrough of the 7-line `NormalDist` calculation.
- `docs/conversation_transcript.md` — Full chat export (private).

### B. AI Control Project (`ai-control-project/`): Main Shareable Project
- Phase 0 toy simulation and Phase 1 experiment (30 code diffs). Result: separation `2.202`, exploit viability `0.600`; at a 5% audit budget the Gaussian model gives `80.4%` safety, measured `91.7%`. `atk_12` is the one working attack that slipped through.
- Scrubbed of local paths and employer document IDs. Runs in **snapshot mode** from `results/autohex_exp_results.json` with no private repo. Set `AUTOHEX_REPO` to a local clone of `010.AutoHex` for live re-scoring.
- README lists the limitations (`n=15`, monitor rules written knowing the attacks, author as red team). Keep **private** and share on request.

### C. `publish/`
- `beam-model-validation/`: Checked synthetic Euler–Bernoulli beam dataset, LoRA PoC training, and analytical validation (`README.md` + `.gitignore` added; fabricated support email removed from `implementation_guide.md`). Keep private and share on request.
- `phd-lightning-surrogate/`: Pseudocode only; **private; Prof. Adrian Murphy's (first PhD supervisor) approval needed before outside sharing**.
- **Removed (employer-related risk):** `fdt-localai/`, `agent-loop/`. Originals remain in `C:\Bask\00.AI\013.LocalAI` and `016.24x7_Agent`. Earlier commits remain in this private repo's git history, so never make this top-level repo public.

---

## 2. Next Steps
1. Visually check `cv/Baskaran_Nagavel_AI_Safety_CV.pdf` and confirm whether A220/Transport Canada wording stays or should be generalised.
2. Give **Prof. Adrian Murphy** and **Karthikeyan Gopalakrishnan** a heads-up and add their email/phone numbers when filling Greenhouse.
3. Submit the application to [AI Safety & Security (`5183044008`)](https://job-boards.greenhouse.io/anthropic/jobs/5183044008) using `docs/greenhouse_application_answers.md`.
4. *(Later)* Create `ai-control-project` as its own **private** GitHub repo (copy folder, fresh `git init`) if sharing with interviewers, and run Phase 2 (local LLM monitor via `--ollama-model` + defer-to-trusted).
