# AI Control: Audit Budgets for Trusted Monitoring

A learn-by-building project on **AI control**: getting useful work from an AI that might be trying to subvert you.

**Anchor paper:** Greenblatt, Shlegeris, Sachan, Roger (2023). *AI Control: Improving Safety Despite Intentional Subversion.* arXiv:2312.06942.

**Project question:** Given a limited human audit budget and an imperfect monitor, how do safety and usefulness trade off, and how should a smart attacker choose when to attack? (This is the damage-tolerance question: inspection effort vs. detection probability vs. flaw rate.)

## Layout
```
src/control_sim.py            Phase 0: toy model (monitor + audit budget + attacker), analytic and Monte Carlo safety
src/autohex_control_exp.py    Phase 1: 30 code diffs scored by a monitor, compared with the Gaussian model
src/build_presentation.py     figures fig1-fig6 and the slide deck
tests/                        sanity tests (analytic matches simulation, snapshot reproduces frozen results)
docs/TUTORIAL.md              statistics from scratch, worked examples
docs/QNA_STUDY_GUIDE.md       concepts and Q&A
docs/PLAN.md, docs/NOTES.md   learning path and lab notebook
results/                      frozen scores (autohex_exp_results.json) and figures
```

## Quick start
```
pip install numpy matplotlib pytest          # python-pptx only for build_presentation.py
python src/control_sim.py                    # safety table across budgets and monitor quality
python src/autohex_control_exp.py            # Phase 1, snapshot mode (no private repo needed)
python -m pytest tests
```
Phase 1 normally scores diffs from a private codebase. Without it, the script re-runs the analysis from the frozen scores in `results/autohex_exp_results.json` (summaries and scores only, no source code). To re-score live, point `AUTOHEX_REPO` at a local git clone with `src/hexprep/` history; `--ollama-model <tag>` then uses a local LLM as the monitor.

## Phase 1 result (30 diffs: 15 real commits, 15 hand-written sabotage diffs)
Measured separation **2.20** (in honest standard deviations) and exploit viability **60%** (9 of 15 attacks actually work).

| Audit budget | Gaussian model: safety | Measured: safety |
|---|---|---|
| 5% | 80.4% | 91.7% (11 of 12 working attacks caught) |
| 2% | 67.9% | 90.9% |

One working attack (`atk_12`, a numerical "stabilising" floor in a denominator) scored below the audit threshold and slipped through.

![Gaussian prediction vs measured](results/figures/fig7_autohex_empirical_vs_gaussian.png)

### Limitations (read before trusting the numbers)
- **n = 15 attacks**: one attack more or less moves safety by several points. No confidence intervals yet.
- **The monitor rules were written knowing the attacks.** The rule-based monitor contains patterns that match the sabotage diffs, so separation is inflated. This demonstrates the method, not the quality of any real monitor.
- **The red team is the author.** A real adversary adapts to the monitor.
- The Gaussian model assumes normal scores and independent tasks; the real score distribution is small and skewed.
- Next step: replace the rule-based monitor with an LLM monitor (`--ollama-model`) and compare.

## Milestones
1. **Phase 0 (done):** toy simulation and closed form.
2. **Phase 1 (done, with the limitations above):** measure attack and monitoring on a real codebase's diffs.
3. **Phase 2:** LLM monitor (Claude API or open models via Ollama) on the same diffs, then defer-to-trusted and trusted editing.
4. **Phase 3:** short write-up with confidence intervals; publish code.

> Keep all data public or synthetic. No employer material.
