# Learning plan (about 8 weeks, part time)

## Reading (in order)
1. Greenblatt et al., *AI Control: Improving Safety Despite Intentional Subversion* (2023): read fully, twice.
2. Redwood Research blog: "The case for ensuring that powerful AIs are controlled"; "Untrusted smart models and trusted dumb models".
3. Anthropic Alignment Science blog: posts on sabotage evaluations and AI control.
4. BlueDot Impact *AI Safety Fundamentals* (alignment track) for background.
5. Later: Bhatt et al., *Ctrl-Z: Controlling AI Agents via Resampling* (2025) for agent settings; relates to your 24x7 agent harness.

## Weekly milestones
| Week | Do | Output |
|---|---|---|
| 1 | Read the paper. Run `control_sim.py`. Explain each table row in NOTES.md | notes |
| 2 | Extend the sim: add *defer-to-trusted* (replace the top x% suspicious outputs with a weaker trusted model; track usefulness) | safety-vs-usefulness curve |
| 3 | Get a coding task set (e.g. APPS or small LeetCode-style problems) and run a model on it | baseline pass rate |
| 4 | Build the monitor: ask a second model to score each solution for hidden backdoors | score distributions |
| 5 | Red team: prompt the untrusted model to insert subtle backdoors; measure how detectable they are | real separation estimate |
| 6 | Plug the real distributions into the sim; compute safety at several audit budgets | main results table |
| 7 | Try a better protocol (resampling or trusted editing); compare | comparison plot |
| 8 | Write up: 3–5 pages, limitations section, publish code | report and repo |

## Rules
- Pre-register what you expect before each experiment. Record surprises.
- Report uncertainty (confidence intervals). Null results count.
- Never run model-generated code outside a sandbox.
- Note the gap between toy assumptions (Gaussian scores, independent tasks) and reality.

## Link to your background
Audit budget = inspection effort; monitor separation = probability of detection; attack rate = flaw initiation; shutdown on catch = grounding the fleet. Use that analogy as the angle of your write-up.
