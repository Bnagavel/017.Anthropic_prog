# AI Control: Audit Budgets for Trusted Monitoring

A learn-by-building project on **AI control**: getting useful work from an AI that might be trying to subvert you.

**Anchor paper:** Greenblatt, Shlegeris, Sachan, Roger (2023). *AI Control: Improving Safety Despite Intentional Subversion.* arXiv:2312.06942.

**Project question:** Given a limited human audit budget and an imperfect monitor, how do safety and usefulness trade off, and how should a smart attacker choose when to attack? (This is the damage-tolerance question: inspection effort vs. detection probability vs. flaw rate.)

## Layout
```
src/control_sim.py     toy model: monitor + audit budget + attacker, analytic & Monte Carlo safety
tests/                 sanity tests (analytic matches simulation, monotonicity)
docs/PLAN.md           learning path, reading list, milestones
docs/NOTES.md          running lab notebook (write here every session)
results/               plots and tables
```

## Quick start
```
python src/control_sim.py          # safety table across budgets and monitor quality
python -m pytest tests             # needs: pip install pytest
```

## Milestones
1. **Phase 0 (done):** toy simulation and closed form (this repo).
2. **Phase 1:** reproduce the paper's *trusted monitoring* and *untrusted monitoring* ideas with real LLMs on coding tasks (Claude API or open models via Ollama).
3. **Phase 2:** measure how good an LLM monitor actually is (replace the Gaussian `separation` with real score distributions).
4. **Phase 3:** write up a short report; publish code and post.

> Keep all data public or synthetic. No employer material.
