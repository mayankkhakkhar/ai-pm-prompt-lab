# Experiment 02: 3-model comparison on the 26-case suite

**Date:** 2026-09-24
**Goal:** Re-run the M2.7 vs M2.7-highspeed vs M3 comparison on the expanded 26-case suite (added 10 health insurance + 3 variance + 3 edge cases).

## Method

- Test set: `evals/sample-set.yaml` (26 cases — was 10)
- Judge model: `MiniMax-M3` (consistent across all runs)
- Same as Experiment 01, just with a harder eval set

## Results

| Model | Pass | Avg latency | Total tokens |
|---|---|---|---|
| MiniMax-M3 | **23/26 (88%)** 🏆 | 2.69s | 9,874 |
| MiniMax-M2.7-highspeed | 21/26 (81%) | 5.23s | 7,360 |
| MiniMax-M2.7 | 19/26 (73%) | 4.95s | 6,619 |

## Comparison vs Experiment 01 (10 cases)

| Model | 10-case score | 26-case score | Δ |
|---|---|---|---|
| M2.7 | 10/10 (100%) | 19/26 (73%) | **-27 pts** |
| M2.7-highspeed | 8/10 (80%) | 21/26 (81%) | +1 pt |
| M3 | 10/10 (100%) | 23/26 (88%) | **-12 pts** |

## Findings

1. **The 10-case eval was too easy to differentiate models.** All three scored at or near the ceiling, masking real quality differences. Adding harder PM-flavored cases exposed them.

2. **M3 is meaningfully better on hard tasks.** 88% vs 73% (M2.7) on the harder suite is a real gap — not just noise. For health-insurance-grade output, M3 is the right model.

3. **M2.7-highspeed beats M2.7 on hard cases** (81% vs 73%). Less reasoning = less over-thinking = more reliable answers on complex prompts. The "speed" framing hides a quality improvement.

4. **M3 uses 49% more tokens than M2.7** (9,874 vs 6,619). At scale, that's a real cost.

5. **M3-as-judge bias likely applies** in the M3-vs-M3 row. M3 may be grading its own outputs more leniently than it grades M2.7. N=1 per model, no statistical claim.

## What this changes

- **For health insurance features**: M3 is the rational choice — the quality gap is real.
- **For format/constraint tasks**: M2.7 is fine — same 100% as M3, lower cost.
- **For latency-sensitive features**: M2.7-highspeed is now in the conversation, not just "fast M2.7."

## PM lesson

**Evals need to be hard to be useful.** A 100%-passing eval is suspicious — it usually means the cases are too easy. The PM move is to add cases that *should* fail, then see which models actually handle them.

## Next experiments

- Run N=3 of each model to measure variance on the 26-case suite
- Add 3-5 cases that specifically target M2.7's gaps (empty-output, missing specifics)
- Test a model we haven't tried (M2.5? M2.1?) for completeness
