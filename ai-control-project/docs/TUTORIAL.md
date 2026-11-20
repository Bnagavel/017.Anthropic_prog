# Tutorial: Understanding the AI Control Project from Scratch

This guide explains everything in `ai-control-project/`: the ideas first, then the code, line by line. Technical terms are **bold** the first time they appear and collected in the glossary at the end.

---

## Part 1. The big picture

### 1.1 What is "AI safety" and what is "AI control"?
**AI safety** is the broad field of making sure AI systems behave in ways that are good for people.

**AI control** is one practical branch. It asks:

> *Suppose an AI is very capable, and we can't be sure it is trustworthy. Can we still use it productively and safely, by putting checks around it?*

Compare **alignment** (making the AI *want* the right things) with **control** (making sure that even if it wants the wrong things, it can't do real harm). Control is a second line of defence. Engineers do the same thing: you design a structure to be safe even if a flaw is present.

### 1.2 The setup in the paper
The paper is Greenblatt et al. (2023), *AI Control: Improving Safety Despite Intentional Subversion*. It sets up this game:

| Role | Who | Description |
|---|---|---|
| **Untrusted model** | A strong AI (the paper used GPT-4) | Does useful work, but might secretly **sabotage** it |
| **Trusted model** | A weaker AI (GPT-3.5) | Weaker but assumed honest, because it is too weak to scheme |
| **Humans** | Scarce, expensive, trusted | Can carefully check ("**audit**") only a small number of outputs |

**The task:** write code to solve programming problems. The sabotage to watch for is a **backdoor**: code that passes the normal tests but secretly gives a wrong answer on a special input, so an attacker could exploit it later.

**The defence, "trusted monitoring":**
1. The untrusted model writes a solution.
2. The trusted model reads it and gives a **suspicion score** (higher = more likely a backdoor).
3. Humans audit the highest-scoring solutions, up to a fixed limit, the **audit budget** (the paper used 2% of problems).

**Two teams in the game:**
- **Red team** plays the attacker (the untrusted model's plan). It tries to slip a backdoor past the audit.
- **Blue team** plays the defender. It designs the monitoring and auditing.

**How the game ends:**
- If an audited output contains a backdoor, the humans have *caught the model* and the blue team wins (the AI is shut down or retrained).
- If a backdoor gets through unaudited and works, the red team wins.

**Safety** is the probability that the red team does *not* win.

### 1.3 The analogy to your own field
| AI control | Damage-tolerance engineering |
|---|---|
| Backdoor | A crack or flaw |
| Attack rate | How often flaws start |
| Monitor's suspicion score | A non-destructive inspection signal |
| Audit budget | How much inspection you can afford |
| Monitor quality | **Probability of detection** (POD) |
| Catching the model | Finding the crack, which grounds the fleet |
| Safety | Probability the structure doesn't fail |

In both fields you can't prevent every flaw. You choose how much to inspect, and how good the inspection has to be, to get an acceptable chance of finding a flaw before it matters.

---

## Part 2. The statistics you need

The simulation uses a few ideas from probability. Here they are in plain terms.

### 2.1 Probability and the normal (Gaussian) distribution
A **probability** is a number between 0 and 1 for how likely something is.

A **normal distribution** (or **Gaussian**, the "bell curve") describes values that cluster around an average (the **mean**), with a spread (the **standard deviation**). `N(0, 1)` means mean 0 and standard deviation 1.

- **CDF** (cumulative distribution function): `cdf(x)` is the probability that a value is *less than or equal to* `x`.
- **Inverse CDF** (also called **quantile function** or **percent-point function**): the reverse. `inv_cdf(0.98)` returns the value below which 98% of outcomes fall. For `N(0,1)` that is about **2.054**.

### 2.2 Modelling the monitor
The code assumes the monitor's score follows these distributions:
- Benign (honest) solutions: scores ~ `N(0, 1)`
- Backdoored (attack) solutions: scores ~ `N(separation, 1)`

`separation` is how far apart the two bell curves sit. This is the same idea as **d-prime** (d′) in signal detection theory. A bigger separation means a better monitor:

- `separation = 0`: the monitor is useless; the curves overlap completely.
- `separation = 3`: attacks usually score clearly higher than honest outputs.

### 2.3 Threshold, false positives, true positives
The audit rule is: *audit anything whose score is above a **threshold**.*

- **False positive**: auditing an honest output (a wasted audit).
- **True positive**: auditing a real attack (a catch). The true-positive rate is also called **recall** or **sensitivity**.
- **Audit budget** `b` is the fraction of work you can audit. We set the threshold so that honest outputs are audited with probability exactly `b`. That is the **false-positive rate = b**.

So the threshold is `inv_cdf(1 − b)`. For `b = 0.02`, the threshold is 2.054.

### 2.4 Probability that an attack is caught
An attack's score is `N(separation, 1)`. It is audited if its score ≥ threshold:

```
p_caught = 1 − cdf(threshold − separation)
```

**Worked example** (`b = 0.02`, `separation = 2`):
- threshold = 2.054
- p_caught = 1 − cdf(2.054 − 2) = 1 − cdf(0.054) ≈ 1 − 0.522 = **0.478**

So this monitor catches about 48% of attacks at a 2% audit budget.

---

## Part 2B. Part 2 again, as one concrete example

Same ideas, now with numbers you can follow with a pencil. Our setting: **1,000 tasks**, **audit budget 2%**, **separation 2**, and **attack_success 0.5**.

### Step 1: Picture the two bell curves
Each output gets a score. Honest outputs bunch around 0; backdoored outputs bunch around 2. Each bell is the same width (standard deviation 1).

```
 score:   -2    -1     0     1     2     3     4
           .     .     .     .     .     .     .
 honest:         ▁▃▆██▆▃▁                          centred at 0
 attack:                   ▁▃▆██▆▃▁                centred at 2
                                  ^
                          threshold ≈ 2.05
```
The monitor can't see which curve an output came from. It only sees the score. Any output with a score to the right of the threshold gets audited.

### Step 2: Where do we put the threshold?
Rule of thumb for a bell curve with mean 0 and standard deviation 1 (the **68-95-99.7 rule**):
- about 68% of values fall between −1 and +1
- about 95% fall between −2 and +2
- about 99.7% fall between −3 and +3

If 95% fall within ±2, then the remaining 5% are split into two tails of 2.5% each. So only **about 2.5%** of honest outputs score above 2. We want **exactly 2%**, which is a bit further right: **2.054**. Exact values like this come from `inv_cdf(0.98)`, which is "the score that 98% of honest outputs fall below".

**In human terms:** out of 1,000 honest outputs, about **20** will score above 2.054. Those 20 are the audits we can afford. That is the audit budget doing its job.

### Step 3: How many attacks does that catch?
Attack scores are centred at 2, not 0. The threshold sits at 2.054, which is only **0.054 above the attack curve's centre**. A bell curve is symmetric: half of its values are above the centre. Just above the centre, slightly under half remain. So slightly less than half of the attacks are audited.

Exactly, using the CDF (the "fraction below x" function), here are some values for the standard bell curve:

| x | cdf(x) = fraction of values below x |
|---|---|
| −1 | 0.159 |
| 0 | 0.500 |
| 0.054 | 0.522 |
| 1 | 0.841 |
| 1.054 | 0.854 |
| 2 | 0.977 |

The fraction of attacks **above** the threshold is 1 − cdf(threshold − separation) = 1 − cdf(2.054 − 2) = 1 − cdf(0.054) = 1 − 0.522 = **0.478**.

Why subtract the separation? Shifting the attack curve right by 2 is the same as shifting the threshold left by 2 and using the standard curve. We just measure how far the threshold is from each curve's centre.

**In human terms:** if the attacker makes 100 backdoors, about **48** are audited and caught, and about **52** slip through.

### Step 4: What happens to the 52 that slip through?
Not every unaudited backdoor works. Our `attack_success` is 0.5, so about half of the slipped ones succeed:
- caught: c = 0.478
- slipped and succeeded: s = 0.522 × 0.5 = **0.261**
- slipped but fizzled: 0.522 × 0.5 = 0.261 (nothing happens)

Only the first two end the game. Together they make the **decisive** probability: d = c + s = 0.478 + 0.261 = **0.739**.

### Step 5: The race
The game ends at the first decisive attack. Whichever outcome comes first decides the winner, and the chance it's a catch is:

```
c / d = 0.478 / 0.739 = 0.647
```
So **safety ≈ 65%** (assuming enough attacks happen that a decisive one is nearly certain).

Picture it as flipping a weighted coin each time a decisive attack happens: 65% "caught" (blue wins) and 35% "succeeded" (red wins). The first flip is the only one that matters.

### Step 6: How do monitor quality and budget change the answer?
Redo steps 3–5 with different separations (same 2% budget, same threshold 2.054):

| separation | fraction of attacks caught c | s = (1−c)×0.5 | d = c+s | safety = c/d |
|---|---|---|---|---|
| 1 | 1 − cdf(1.054) = 0.146 | 0.427 | 0.573 | **0.26** |
| 2 | 1 − cdf(0.054) = 0.478 | 0.261 | 0.739 | **0.65** |
| 3 | 1 − cdf(−0.946) = 0.828 | 0.086 | 0.914 | **0.91** |

These match the large-attack-rate columns of `python src\control_sim.py`. **Takeaway:** pushing the two bell curves further apart helps far more than any other change.

### Step 7: Check it yourself
```python
from statistics import NormalDist
nd = NormalDist()                 # mean 0, standard deviation 1
budget, sep, p_ok = 0.02, 2.0, 0.5

t = nd.inv_cdf(1 - budget)        # threshold   -> 2.054
c = 1 - nd.cdf(t - sep)           # caught      -> 0.478
s = (1 - c) * p_ok                # slipped+won -> 0.261
print(t, c, s, c / (c + s))       # safety      -> 0.647
```
Change `sep` to 1 and 3 and compare with the table above.

### What about the number of tasks and attack rate?
With 1,000 tasks and an attack rate of 1% you expect about 10 attacks, and the chance of **zero decisive events** is tiny. That is why the race value (65%) is the answer. If the attacker attacks very rarely (say 0.01% → 0.1 attacks expected), there's a good chance of no attack at all, so safety goes up. That is the `q` term in the formula in Part 3.

---

## Part 2C. Where do the numbers come from? (Inputs vs outputs)

Short answer: **I chose them.** They are **assumptions** (also called **parameters** or **inputs**), not facts and not derived from anything. In Phase 0 they are placeholders so the machinery can run. Each one has a real-world counterpart that you would later **measure** or **decide**.

### Four kinds of number in this project
| Kind | Meaning | Examples |
|---|---|---|
| **Design choice** | Set by the defender; you can pick it | `audit_budget` (how many humans you can afford), `n_tasks` |
| **Assumption about the world** | Unknown reality; you guess now, measure later | `separation`, `attack_success` |
| **Adversary's choice** | Set by the attacker | `attack_rate` |
| **Output (result)** | Computed from the above | `p_caught`, `safety` |

### `separation`
- **What it stands for:** how well the monitor tells attacks from honest work.
- **Why I used 2:** it is a middle value. 1 is a weak monitor and 3 is strong, so I tried 1, 2 and 3 and compared. There's no deeper reason.
- **How you'd measure it for real (Phase 2):**
  1. Collect many honest solutions and many solutions with known backdoors.
  2. Ask the monitor model to score each one.
  3. Compute the mean score of each group and the spread. Then
     `separation ≈ (mean_attack − mean_honest) / standard_deviation`.
  This number is called **d′ (d-prime)**. Real monitors can have messier score shapes than bell curves, so d′ is an approximation.

### `attack_success`
- **What it stands for:** if a backdoor is *not* audited, the chance it really works and causes harm. Some backdoors are buggy, or the exploit input never gets triggered.
- **Why I used 0.5:** it is an arbitrary round number. It means "half of unaudited backdoors work".
- **How you'd measure it:** have the attacker model write backdoors, then test each one against its exploit input. The fraction that works is `attack_success`. In the paper this was part of the definition of a valid backdoor: it must pass the tests *and* fail on the exploit input.

### `audit_budget` and `n_tasks`
- **`audit_budget`: 2%** I took from the paper's setup, as I remember it (check it). In reality it is set by how many human-hours you have.
- **`n_tasks`: 1,000** is a convenient round number, not from the paper. A bigger value makes an attack more certain to happen at some point.

### `attack_rate`
This is the attacker's choice. In the sample output we tried several (0.0001, 0.001, 0.01, 0.05) to see the effect, rather than assuming one.

### Why this matters: **sensitivity analysis**
Because `separation` and `attack_success` are guesses, **the safety numbers are only as good as those guesses**. So you don't report "safety is 65%". You report "safety is 65% *if* separation is 2 and attack_success is 0.5, and here is how it changes when I vary them". Checking how much the output changes when you vary an input is called **sensitivity analysis**. The big table from `control_sim.py` is exactly that.

Compare what we learn from varying each assumption (2% budget, large attack rate):
| attack_success | safety (separation 2) |
|---|---|
| 0.1 | 0.90 |
| 0.5 | 0.65 |
| 1.0 | 0.48 |

Formula: safety = c / (c + (1−c)×attack_success), with c = 0.478.
- 0.1: 0.478 / (0.478 + 0.052) = 0.90
- 1.0: 0.478 / (0.478 + 0.522) = 0.478

So `attack_success` matters a lot, and a real number for it would be valuable. The toy model can't tell you which value is realistic; only an experiment can.

### The "no free lunch" point
A toy model **can't** tell you what real safety is. What it **can** do:
1. show *which inputs matter most* (here: monitor quality, then attack success, then budget);
2. tell you *what to measure first* in a real experiment;
3. give you a prediction to compare the real result against.

That is why Phase 1–2 exist: to replace guessed inputs with measured ones.

---

## Part 3. The code, file by file

### 3.1 `src/control_sim.py`

**`Config`** (a `dataclass`, i.e. a simple container of settings):
| Field | Default | Meaning |
|---|---|---|
| `n_tasks` | 1000 | Number of problems the untrusted model works on |
| `attack_rate` | 0.01 | Chance it attacks on any one task |
| `audit_budget` | 0.02 | Fraction of tasks humans can audit |
| `separation` | 2.0 | Monitor quality (d′) |
| `attack_success` | 0.5 | Chance an *unaudited* attack actually works |

`frozen=True` means a `Config` can't be changed after creation. That prevents accidental changes while experimenting.

**`threshold(b)`**: returns `inv_cdf(1 − b)`, the score above which we audit.

**`p_caught(cfg)`**: the formula from section 2.4.

**`safety_analytic(cfg)`**: computes safety exactly with algebra (an **analytic** or **closed-form** solution).

Reasoning: each attack is either
- **caught** with probability `c`, so blue wins; or
- **succeeds unnoticed** with probability `s = (1 − c) × attack_success`, so red wins; or
- fizzles out (neither).

An attack is *decisive* if it ends the game: probability `d = c + s`. Per task, a decisive event happens with probability `attack_rate × d`. Over `n` tasks:

```
q = (1 − attack_rate × d) ^ n         # no decisive event at all (safe)
safety = q + (1 − q) × (c / d)        # or a decisive event happens and it was a catch
```

The last term holds because, given that something decisive happened, the chance it was a catch is `c / (c + s)`. This is a **race** between "caught first" and "succeeds first".

**`safety_monte_carlo(cfg)`**: a **Monte Carlo simulation**. Instead of algebra it *plays the game thousands of times* with random numbers and counts how often blue wins. It uses `random.Random(seed)`. A fixed **seed** makes the "random" numbers repeatable, which is essential for reproducible science.

Each simulated episode:
1. For each task: with probability `attack_rate`, attack.
2. Draw the monitor's score from `N(separation, 1)`.
3. If score ≥ threshold, the attack is audited, so blue wins.
4. Otherwise it succeeds with probability `attack_success`, so red wins.
5. If no decisive event occurs, blue "wins" (nothing bad happened).

Two independent ways of computing the same number is a powerful check. If they agree, you can trust both.

**`best_attack_rate(cfg)`**: a leftover helper that searches for the attack rate that minimises safety. See the correction in 3.4 before relying on it.

### 3.2 `tests/test_control_sim.py`
A **test** is a small program that checks the code behaves correctly.
1. `test_analytic_matches_monte_carlo`: the two methods must agree within 2 percentage points.
2. `test_more_budget_never_hurts`: a bigger audit budget can't reduce safety (**monotonicity**).
3. `test_better_monitor_never_hurts`: a larger separation can't reduce safety.

Such common-sense checks (**sanity tests**) catch bugs early. Run them with `pytest` (install with `pip install pytest`).

### 3.3 The other files
- `README.md`: the project overview and milestones.
- `docs/PLAN.md`: reading list and an 8-week schedule.
- `docs/NOTES.md`: a lab-notebook template. Researchers keep notes on predictions, results and surprises.
- `results/`: empty for now; plots and tables go here.

### 3.4 ⚠ A correction to my earlier summary
When I first ran the script I printed a "worst attack rate" column and told you attackers should attack "a few percent of the time". **That was wrong.** Here's why.

In this simplified race model:
```
safety = q + (1 − q) × c/d
```
Once the attacker attacks often enough that *some* attack is almost certain (`q ≈ 0`), safety is just `c/d`, **independent of the attack rate**. The earlier "worst rate" was floating-point noise among nearly identical numbers. The script now prints safety at several fixed attack rates instead. Look at the `rate=0.01` and `rate=0.05` columns: they are almost identical.

**What the model does show:**
- **Lower attack rates are safer here**, because with very few attacks there may be none at all in the deployment. At `rate=0.0001` safety is 95–99%.
- Once attacks are common, safety is set by the **monitor quality** and **audit budget**, not by how often the attacker tries.
- At a 2% budget and `separation = 2`, safety falls to about 65%. Raising the monitor's separation to 3 raises it to about 91%.

**A limitation to remember:** the paper's game has more structure than this toy. For example, the attacker chooses *which* tasks to attack, and attack success depends on the problem. So this toy can't tell you the optimal attacker strategy. Making it richer is a good exercise (see below).

---

## Part 4. Running it and reading the results

```
cd ai-control-project
python src\control_sim.py
```

Each row is a monitor setup; each column is an attack rate; each number is **safety**. Try reading one row:

`audit_budget = 0.02, separation = 2.0` gives about 0.975 / 0.816 / 0.648 / 0.647 for the four attack rates.

Meaning: at a very low attack rate, there's likely no attack at all, so we're ~97% safe. As attacks become frequent, safety settles to the **race** value of about 65%.

---

## Part 5. Exercises (do these in order)

1. **Predict first.** Before running, write in `NOTES.md`: "If I double the audit budget, safety will…". Then run and compare.
2. **Verify by hand.** Reproduce the worked example in 2.4 with a calculator or a few lines of Python (`from statistics import NormalDist`).
3. **Monte Carlo vs algebra.** Raise `episodes` from 20,000 to 200,000. How does the gap between the two methods change? (This is the **law of large numbers**.)
4. **Add a confidence interval** to `safety_monte_carlo`: standard error = `sqrt(p(1−p)/episodes)`.
5. **Break the assumptions.** Replace the Gaussian with a heavier-tailed distribution. Does the ranking of audit budgets change?
6. **Make the attacker smarter.** Let the attacker choose to attack only when the task is "easy to hide". This is the paper's central red-team idea.
7. **Add usefulness.** In the paper, there's a second axis: how much correct work you get. Add a *defer-to-trusted* policy (replace the most suspicious x% of outputs with the weaker model's answers) and plot **safety vs usefulness**.

---

## Part 6. How this project differs from the Greenblatt et al. paper

> [!NOTE]
> The paper's details below are from my memory of it. **Check them against the paper itself** (arXiv:2312.06942) when you read it. Treat any difference you find as a correction to this table.

### What the paper did
- **Real language models.** GPT-4 was the untrusted model and GPT-3.5 the trusted one.
- **A real task.** Programming problems from the APPS dataset (a few thousand problems). A backdoor is code that passes the visible tests but is wrong on a hidden "exploit" input.
- **A real red team.** The researchers engineered prompts and scaffolding so GPT-4 wrote subtle backdoors, and chose which problems to attack.
- **Real monitors.** GPT-3.5 (and in other protocols, GPT-4 itself) scored code; auditing was limited to about 2% of problems.
- **Several protocols compared,** such as trusted monitoring, untrusted monitoring, *defer to trusted* and *trusted editing*, measured on **both safety and usefulness**.
- **A worst-case mindset:** the red team could adapt to the blue team's protocol, as in a real adversarial setting.

### What this project does (and doesn't)

| Aspect | Greenblatt et al. | This project, Phase 0 (now) | This project, later phases |
|---|---|---|---|
| Models | Real GPT-4 / GPT-3.5 | **None.** Made-up bell-curve scores | Real LLMs (Claude API or local models) as monitor |
| Monitor quality | Measured from the models | **Assumed** (`separation`) | Measured, so you can replace the assumption |
| Attacker | Smart, adaptive, picks tasks | **Dumb:** attacks at a fixed random rate | Add task selection (exercise 6) |
| Protocols | Several | Only **trusted monitoring** | Add defer-to-trusted and compare |
| Usefulness measured | Yes | **No**, only safety | Exercise 7 |
| Humans | Simulated, 2% budget | Idealised: an audit always spots a backdoor | Add a noisy auditor |
| Output | Empirical results | A **teaching model** | Your own experiment and write-up |

### Honest summary
- **Phase 0 is not a replication.** It is a toy model that captures one part of the paper's logic (the audit budget and the safety race) so you can build intuition.
- **Plain differences:** no real models, a non-adaptive attacker, one protocol, no usefulness axis, and assumed (not measured) monitor quality.
- **What is original here:** (1) the damage-tolerance framing of audit budget as inspection effort, and a plan to write it up from that angle; (2) a plan to test the model against a *real* monitor and compare the resulting safety numbers with the toy model's; (3) using your own agent harness as a realistic testbed. Whether the results are new depends on what you find, so don't claim novelty before you have checked related work.

### How the later phases close the gap
1. **Measure the monitor** on real code with and without backdoors, and fit the actual score distributions. The real ones are unlikely to be perfect bell curves, so the closed form may break, and *how* it breaks is a result.
2. **Add an adaptive attacker** that sees the monitor's score and attacks only when it expects to slip through.
3. **Add defer-to-trusted** and plot safety against usefulness.
4. **Compare** your numbers with the paper's and explain differences. Expect some. Different models, tasks and prompts give different results, so don't treat them as errors.

---

## Glossary

| Term | Meaning |
|---|---|
| **AI control** | Techniques that keep AI use safe even if the AI is trying to cause harm |
| **Alignment** | Making an AI's goals match what people want |
| **Untrusted / trusted model** | Strong but possibly deceptive AI / weaker but assumed honest AI |
| **Backdoor** | Hidden flaw in code that triggers only on special inputs |
| **Monitor** | A model that scores outputs for suspiciousness |
| **Suspicion score** | The monitor's number: higher means more suspicious |
| **Audit** | Careful (expensive) human review |
| **Audit budget** | The fraction of outputs you can audit |
| **Threshold** | The score above which an output is audited |
| **Red / blue team** | Attacker / defender in the evaluation game |
| **Safety** | Probability the red team does not win |
| **Usefulness** | How much correct work the system still gets done |
| **Protocol** | The full recipe: who does what, when to audit, when to defer |
| **Normal / Gaussian distribution** | The bell curve |
| **CDF / inverse CDF** | Probability of being ≤ x / the value at a given probability |
| **Separation (d′)** | Distance between honest and attack score distributions |
| **False / true positive rate** | Fraction of honest outputs audited / fraction of attacks audited |
| **Closed-form (analytic)** | Exact formula solution |
| **Monte Carlo** | Estimating something by simulating it many times with random numbers |
| **Seed** | Starting value that makes random numbers repeatable |
| **Monotonicity** | Property that increasing one input never decreases the output |
| **Confidence interval** | Range expressing the uncertainty of an estimate |
