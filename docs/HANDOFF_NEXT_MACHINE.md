# Session Handoff — Anthropic Fellows Program & AI Control Study

Use this file to resume immediately on your next machine (either yourself or by pointing a fresh AI assistant to `docs/HANDOFF_NEXT_MACHINE.md`).

> **CRITICAL PRIVACY WARNING BEFORE PUSHING TO GITHUB:**
> This top-level folder (`017.Anthropic_prog/`) contains personal CVs/cover letters (including phone/email/passport info in `Baskaran_Nagavel_Resume_2025.docx`), training certificates, and the full private chat log.
> - Push `017.Anthropic_prog/` **ONLY to a PRIVATE GitHub repository** for syncing between your machines.
> - Only the sanitized sub-folders inside `publish/` (`fdt-localai/`, `agent-loop/`, `beam-model-validation/`) and `ai-control-project/` are safe to push as **PUBLIC** portfolio repositories.

---

## 1. Complete Inventory of Stored Files

### A. Strategy, Application Drafts & Full Chat Archive (`docs/`)
- `docs/anthropic_fellowship_recommendation.md` — Track analysis for UK-eligible Anthropic Fellows Program postings:
  - **Primary:** [AI Safety & Security (`5183044008`)](https://job-boards.greenhouse.io/anthropic/jobs/5183044008) — AI Safety Fellows (1. Adversarial Robustness & AI Control, 2. Scalable Oversight).
  - **Optional Secondary:** [The Anthropic Institute (`5183053008`)](https://job-boards.greenhouse.io/anthropic/jobs/5183053008) — Policy, Security & Society.
- `docs/anthropic_application_pack.md` — Draft 1-page AI-focused CV, 250-word motivation statement, research proposal sketch, and publishing checklist.
- `docs/ai_control_stats_presentation.md` — Visual slide-deck walkthrough of the 7-line `NormalDist` AI Control math (links to `../ai-control-project/results/figures/fig1..fig6`).
- `docs/conversation_transcript.md` — Complete 29-turn chronological transcript of our entire conversation (from fellowship recommendation through Greenblatt et al. 2023, `010.AutoHex` Phase 1 experiment, Defer-to-Trusted, Trusted Editing, Untrusted Monitoring / Collusion, Ctrl-Z, Anthropic Sabotage Evaluations, and ControlArena).

### B. Hands-On AI Control Project (`ai-control-project/`)
- `ai-control-project/docs/QNA_STUDY_GUIDE.md` — Structured Q&A study guide covering the core AI Control concepts.
- `ai-control-project/docs/TUTORIAL.md` — Step-by-step statistical & code tutorial (Parts 1–6).
- `ai-control-project/docs/AI_Control_Statistics_Walkthrough.pptx` — 8-slide 16:9 PowerPoint deck.
- `ai-control-project/src/control_sim.py` — Phase 0 toy simulation & closed-form safety calculation.
- `ai-control-project/src/autohex_control_exp.py` — Phase 1 experiment scoring 15 real `010.AutoHex` honest commits + 15 sabotage diffs (`measured sep = 2.202`, `p_ok = 0.600`; at `budget = 0.05`: Gaussian safety `80.4%` vs. Empirical safety `91.7%`, with `atk_12` in `bore_sectors.py` being the single subtle attack that slipped through).
- `ai-control-project/results/autohex_exp_results.json` & `results/figures/fig1..fig7.png` — Saved numerical outputs and all 7 high-res figures.

### C. Sanitized Public-Ready Portfolio Copies (`publish/`)
Already scrubbed of employer/OEM references (`A220`, `Golihat`, `Bombardier`, `Airbus`, local paths) and `.env` secrets:
- `publish/fdt-localai/` (from `013.LocalAI`)
- `publish/agent-loop/` (from `016.24x7_Agent\010.AutoHex_loop`)
- `publish/beam-model-validation/` (from `006.BeamFoundationModel_Training`)
- `publish/phd-lightning-surrogate/` (PhD): **pseudocode and algorithm notes only**, no code or data (unpublished research). Its README says it is public only to share a glimpse. The original PhD repo (`Study_01`) is NOT in this folder and must stay private.

---

## 2. Exact Next Steps on the New Machine

1. **Answer the 4 remaining `[brackets]` in `docs/anthropic_application_pack.md`:**
   - QUB PhD supervisor name / publications (or keep topic only). Dr Scott Millen is the only name found in the thesis workspace
   - Python libraries you are comfortable being quizzed on (e.g., `NumPy, SciPy, Matplotlib, pytest, Pydantic`)
   - Work location preference for the 4 months (London in-person/hybrid, remote from Belfast + travel, or either)
   - Two referees to notify in advance
2. **Update `docs/anthropic_application_pack.md`** to include your completed `ai-control-project` empirical results (`sep = 2.202`, `p_ok = 0.600`, Gaussian vs. empirical safety on `010.AutoHex`).
3. **Export a clean 1-page PDF CV** and prepare copy-paste answers for the Greenhouse form.
4. **Push the 5 clean repos to public GitHub (`github.com/Bnagavel`), each as a new repo with fresh history (check `phd-lightning-surrogate` with your PhD supervisor first):**
   - `ai-control-project`
   - `fdt-localai`
   - `agent-loop`
   - `beam-model-validation`
   - `phd-lightning-surrogate`
5. **Submit application** to [Anthropic Fellows Program, AI Safety & Security (5183044008)](https://job-boards.greenhouse.io/anthropic/jobs/5183044008).
