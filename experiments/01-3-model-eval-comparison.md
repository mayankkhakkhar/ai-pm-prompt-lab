# Experiment 01: 3-model eval comparison

**Date:** 2026-09-24
**Goal:** Compare M2.7, M2.7-highspeed, and M3 on the same 10-case eval set.

## Method

- Test set: `evals/sample-set.yaml` (10 cases: format / knowledge / extraction / classification / qualitative)
- Judge model: `MiniMax-M3` (consistent across all runs)
- Each run = one model tested against all 10 cases
- temperature=0.7 on all calls (default)

## Results

| Model | Pass | Avg latency | Total tokens | Cost signal |
|---|---|---|---|---|
| MiniMax-M2.7 | 10/10 (100%) | 4.59s | 1,583 | baseline |
| MiniMax-M2.7-highspeed | 8/10 (80%) | **2.92s** | 1,586 | faster, lower quality |
| MiniMax-M3 | 10/10 (100%) | 3.90s | **3,812** | 2.4x more tokens |

## Failures

**MiniMax-M2.7-highspeed:**
- `explain_concept` — judge said: "explains compound interest but no analogy included"
- `meeting_summary` — judge said: "only 2 distinct action items, rubric requires 3"

**MiniMax-M2.7:** none
**MiniMax-M3:** none

## Findings

1. **M2.7 is the sweet spot for this eval set** — same quality as M3 at ~40% token cost.
2. **M2.7-highspeed is a quality downgrade, not just a speed upgrade** — 8/10 vs 10/10. The speed/quality trade-off is real.
3. **M3 is more expensive but no better on these tasks** — bigger model doesn't mean better answer for simple prompts.

## Caveats

- **M3 judged itself in run 3** — likely biased. Need a separate judge to compare M3 against M2.7 fairly.
- **M2.7 was 9/10 in an earlier baseline run** — same eval, same model, different score. That's variance. Single-run eval results are point-in-time, not absolute truths.
- **No statistical significance** — N=1 per model. A reliable comparison needs N=3+ runs.

## Next experiments

- Run all 3 models with N=3 (3 runs each) to measure variance
- Test the same eval set with a different judge (e.g., a model we haven't tested)
- Add PM-flavored cases (trade settlement, claim triage) — see if M3 pulls ahead on harder tasks
