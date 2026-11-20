# Anthropic Fellows Program: Which Track Fits You (UK)

*Sources: your CVs, cover letters and certificates in `017.Anthropic_prog`, your GitHub profile, and the live Anthropic Greenhouse postings (checked 9 Nov 2026).*

## 1. Your profile in brief

| Area | Evidence |
|---|---|
| Domain | 16+ years in aerospace structures: fatigue and damage tolerance (F&DT), static stress, FEA (A220, Global 7000, Challenger, Leonardo AW101) |
| Core strength | **Safety-critical certification and verification & validation (V&V)**: building evidence that a structure is safe, writing certification reports for Transport Canada, correlating analysis with tests, setting inspection intervals (ALI) |
| Research | Part-time postgraduate research at Queen's University Belfast (since 2021): *simulation tools for lightning strike protection in composites* |
| Coding | Python, Excel VBA, in-house fatigue/fracture codes, NAFEMS "FEA with Python", MITx *Computational Thinking using Python* |
| Leadership | Technical lead since 2023, mentoring, classroom F&DT training, Best Project Execution award |
| Other certs | Two Baines Simmons certificates (aviation safety and compliance training; one appears to be the CVE course). The text is embedded in a way I couldn't fully extract, so please confirm the course titles |
| Eligibility | Lives in Belfast with UK ILR, so you can work in the UK. **Fellows get no visa sponsorship, so this matters** |
| GitHub | [github.com/Bnagavel](https://github.com/Bnagavel) shows **0 public repositories**. Any repos you have are private and invisible to reviewers |

## 2. Fellows tracks currently open to UK applicants

| Posting | Fit for you | Why |
|---|---|---|
| **[AI Safety & Security](https://job-boards.greenhouse.io/anthropic/jobs/5183044008), AI Safety Fellows** | ⭐ **Best fit (recommended)** | Empirical safety research. Prior ML experience is not required. Has a London shared workspace. Your assurance and V&V mindset maps directly onto it |
| **[The Anthropic Institute (Economics & Policy)](https://job-boards.greenhouse.io/anthropic/jobs/5183053008), Policy, Security & Society** | ✅ **Strong second choice** | Aviation certification is one of the main models people use for AI governance. You'd bring real regulatory-assurance experience. Remote within the UK |
| [ML Systems & Reinforcement Learning](https://job-boards.greenhouse.io/anthropic/jobs/5183051008) | ❌ Not recommended now | Asks for experience building complex ML systems, training or fine-tuning LLMs, and distributed/HPC systems |

All tracks: 4 months full time, **£2,310/week**, about \$15k/month compute, mentoring from Anthropic researchers. Python fluency is **mandatory**.

> [!IMPORTANT]
> **Timing:** The Safety & Security posting says the January cohort deadline was **30 October**. Applications are still reviewed on a rolling basis for later cohorts. The other two postings are accepting applications for the **January 2027** cohort. Apply soon.

## 3. Recommended: AI Safety Fellows, with this framing

**Research areas to choose (in this order):**
1. **Adversarial Robustness & AI Control.** This is the closest match to damage tolerance. You assume a flaw exists (a crack, a misbehaving model), design detection and inspection regimes, and show the system stays safe until the flaw is caught. That is the same logic as AI control protocols and monitoring.
2. **Scalable Oversight / evaluations.** Certification is about building evidence for a safety claim when you can't test everything. That lines up with designing evaluations and **safety cases** for frontier models.
3. *(Optional)* **Model Organisms.** You have built failure models and correlated them with tests, which carries over to deliberately creating misalignment to study it.

**One-line pitch:**
> "16 years certifying safety-critical aircraft structures under damage-tolerance regulations. I want to bring the discipline of safety cases, inspection intervals and test-correlated evidence to the evaluation and control of frontier AI systems."

**Example project ideas to mention:**
- An "inspection interval" model for AI monitoring: how often, and how strongly, to audit agent actions given estimated rates at which failures appear and spread (an analogy to crack-growth / ALI).
- A structured **safety case template for AI deployment**, adapted from aviation certification (CS-25 / FAR 25.571 style), then tested against real evaluation results from open models.
- Benchmarking how reliably LLM agents carry out engineering verification tasks, such as checking stress or fatigue calculations, and how often they make silent errors.

## 4. Gaps to close before you apply

> [!WARNING]
> Reviewers will check Python fluency and look for evidence that you can do empirical ML work. Your GitHub shows nothing public right now.

| Gap | Action (2–6 weeks) |
|---|---|
| No public code | Make 2–3 repos public. Clean up a Python fatigue / crack-growth or FEA post-processing tool (no proprietary data) and add a README |
| No ML/LLM experience | Do one small empirical AI-safety project with open models or the Claude API, e.g. replicate a simple eval or a control/monitoring experiment, and write up the results |
| AI safety background | Work through the BlueDot Impact *AI Safety Fundamentals* course (or ARENA material). Read Anthropic's Alignment Science blog and past Fellows papers |
| Writing sample | Publish a short blog post: *"What AI safety can learn from aircraft damage-tolerance certification"*. It suits the Policy track especially well |
| CV | Write an AI-focused 1-page CV: lead with assurance and V&V, Python, and research (QUB). Cut aircraft part lists down to a few headline results |

## 5. Next steps
1. Confirm the Baines Simmons course titles and whether you can commit full time for 4 months (or note any constraints in the application).
2. Publish code and one small safety experiment.
3. Apply to **AI Safety & Security** (primary). Optionally also apply to **Anthropic Institute – Policy, Security & Society**.
