# Greenhouse Application Answers — Anthropic Fellows Program

**Primary Target Posting:** [Anthropic Fellows Program, AI Safety & Security (`5183044008`)](https://job-boards.greenhouse.io/anthropic/jobs/5183044008)  
**Optional Secondary Posting:** [Anthropic Fellows Program, The Anthropic Institute — Policy, Security & Society (`5183053008`)](https://job-boards.greenhouse.io/anthropic/jobs/5183053008)

---

## 1. Contact & Eligibility Details
- **Full Name:** Baskaran Nagavel
- **Location:** Belfast, United Kingdom
- **Email:** `baskaranpriyan@gmail.com`
- **Phone:** `+44 7404 850176`
- **Work Authorisation:** UK Permanent Resident (Indefinite Leave to Remain) — full right to work in the UK without visa sponsorship.
- **Availability & Location Preference:** Available full-time for the 4-month fellowship. Open to **either** working in London (in-person or hybrid) **or** remotely from Belfast with travel to London as needed.

---

## 2. Track & Research Area Priority
- **Sub-Track:** **AI Safety Fellows**
- **Preferred Research Areas (in priority order):**
  1. **Adversarial Robustness & AI Control** *(primary fit with aviation damage-tolerance certification & audit-interval design)*
  2. **Scalable Oversight / Evaluations** *(building safety-case evidence and verification harnesses)*

---

## 3. CV Attachment
Upload the 1-page PDF generated at:
`cv/Baskaran_Nagavel_AI_Safety_CV.pdf`

---

## 4. Portfolio / GitHub / Code Samples Note *(Optional — only if the online form asks for a GitHub link)*
> My self-directed AI and AI safety experiments (`ai-control-project`, synthetic `beam-model-validation`, and pseudocode algorithm notes for my PhD surrogate modelling in `phd-lightning-surrogate` subject to Prof. Adrian Murphy's approval) are kept in private repositories for now and can be shared if an interviewer asks to see them.

---

## 5. Motivation Statement ("Why are you interested in the Anthropic Fellows Program?")
I have spent 17+ years as an aerospace structural engineer answering one question: *how do we know this structure is safe enough to fly?* Certifying aircraft structures under fatigue and damage-tolerance (F&DT) regulations means assuming flaws will occur, predicting how they grow, correlating analysis against physical tests, and choosing inspection intervals so problems are caught before they compromise safety.

Seeing how significant AI is becoming across aerospace engineering and my part-time PhD research, I started experimenting hands-on with local LLMs and agentic tools out of personal interest. As I explored practical usage—and thought through how to discuss and justify introducing AI tools responsibly with engineering management in a heavily regulated industry—it became clear that capability alone is not enough. Explaining and governing these systems required concrete **AI safety and control** knowledge, and my interest naturally deepened into AI safety because it follows the same underlying logic as aircraft damage-tolerance assurance: monitoring imperfect systems, bounding silent failures, and designing oversight regimes that hold under worst-case assumptions.

Alongside my day job, I began building empirical skills independently. To understand the field practically, I reproduced the trusted-monitoring safety calculation from Greenblatt et al.'s *AI Control* paper and tested it on 30 code diffs from my own meshing codebase (15 real commits and 15 hand-written sabotage diffs) scored by a rule-based monitor. The Gaussian model predicted 80.4% safety at a 5% audit budget against 91.7% measured, though with only 15 attacks and rules tuned knowing them, I treat this strictly as a method check rather than a benchmark—and it taught me how safety hinges on the single subtle attack (`atk_12`) that slips below the threshold. Separately, my QUB PhD builds surrogate models for expensive finite-element simulations, where I validate rigorously on held-out cases and report model breakdowns honestly.

I hold UK Permanent Residency (Indefinite Leave to Remain), can commit full time for four months, and am open to working either in London or remotely within the UK. I would like to contribute to adversarial robustness and AI control, or scalable oversight, and would welcome a full-time role in this field afterwards.

---

## 6. Technical / Research Project Summary (if asked in a short-answer box)
**Empirical AI Control Study (`ai-control-project`) & Surrogate Validation (QUB PhD):**  
To understand AI control protocols practically, I implemented the trusted-monitoring race calculation from Greenblatt et al. (2023) in Python (analytic `NormalDist` closed form and Monte Carlo simulation) and extended it to 30 diffs from an engineering meshing codebase (15 real git commits and 15 constructed specification-gaming/sabotage diffs across obvious, moderate, and subtle tiers). Standardising monitor scores to honest commits (`mean=0, std=1`), I measured separation `2.20` and exploit viability `60%` (`9/15` working exploits). At a 5% audit budget, the Gaussian model predicted `80.4%` safety compared with `91.7%` empirical (`11/12` working attacks caught; one subtle numerical-flooring diff slipped below threshold). Because `n=15` is small and the rule-based monitor knew the attacks, this serves as a baseline method check; the next step is swapping in an untuned local LLM monitor via Ollama and adding defer-to-trusted. Separately, in my QUB PhD on lightning-strike protection in composites (27-run full-factorial DoE, Python/MATLAB automation), I evaluated quadratic, cubic, and GAM surrogates on 5 held-out non-grid geometries—explicitly documenting where quadratic fits failed on severe damage and where GAM achieved `R² = 0.82` yet exhibited non-physical step-wise extrapolation.

---

## 7. Research Proposal Sketch (if asked for proposed fellowship directions)
**Title:** *Audit-interval design for AI monitoring: borrowing damage-tolerance logic for agent oversight*  
In aircraft structural certification, inspectors never assume a zero-defect fleet; instead, they combine an imperfect probability of detection ($a_{\text{det}}$), flaw growth curves, and residual-strength margins to schedule inspection intervals (ALI). Applied to autonomous AI agents, the analogous question is: given a trusted monitor with imperfect separation and a tight human audit budget, how should dynamic audit thresholds, resampling (e.g., *Ctrl-Z*-style action resampling), or defer-to-trusted rules scale across multi-step trajectories where unsafe behaviour accumulates over steps? Using open-weights models and *Inspect* / *ControlArena*-style agent harnesses, I would measure empirical safety-vs-usefulness Pareto curves across varying monitor separation, attack frequency, and trajectory length, alongside failure-case analysis.

---

## 8. Referees (Only if requested in the online form — do NOT put on CV)
> [!IMPORTANT]
> Give both referees a brief heads-up and confirm their preferred **email address** and **phone number** before entering them into Greenhouse. Also double-check the spelling **Prof. Adrian Murphy** (`Adrian`, per QUB directory) before submitting.

1. **Academic Referee / First PhD Supervisor:**  
   **Prof. Adrian Murphy** — Professor of Aeronautical Engineering, School of Mechanical and Aerospace Engineering, Queen's University Belfast  
   *(Email / Phone: add before entering in online form)*
2. **Work / Industry Referee:**  
   **Karthikeyan Gopalakrishnan** — Line Manager, Morson Projects  
   *(Email / Phone: add before entering in online form)*
