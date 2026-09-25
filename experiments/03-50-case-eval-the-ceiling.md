# Experiment 03: 3-model comparison on the 50-case suite

**Date:** 2026-09-25
**Goal:** Expand the suite from 26 to 50 cases and re-run M3 / M2.7-highspeed / M2.7 to see whether the M3 advantage holds up.

## Why this run

The 26-case suite (Experiment 02) showed M3 winning by 15 points over M2.7 (88% vs 73%). Before I published that as a finding, I wanted a larger sample. 26 cases is "promising trend." 50 cases is "tested."

## Method

- Test set: `evals/sample-set.yaml` (50 cases — 26 from before + 24 new in Phase 1.5)
- Judge model: `MiniMax-M3` (consistent across all runs)
- Same harness, same prompt budget, same temperature

## What was added in Phase 1.5 (24 new cases)

- **10 deeper health-insurance cases** — HMO vs PPO, ER vs urgent care, generic vs brand, step therapy, coordination of benefits, No Surprises Act, HSA vs FSA, bronze/silver/gold tiers, EOB line items, medical-advice refusal (safety test)
- **3 extractions** — phone number, dollar amount, date
- **3 classifications** — negative sentiment, urgency (high), intent (question)
- **2 qualitative** — HDHP explanation, ACA premium tax credit
- **3 variance variants** — 4-bullet summary, plus-addressing email, JSON with city/state
- **3 edge cases** — one-word input, numbers-only input, prompt-injection attempt

## Results

| Model | Pass | Avg latency | Total tokens |
|---|---|---|---|
| MiniMax-M3 | **34/50 (68%)** 🏆 | **2.11s** ⚡ | 21,521 |
| MiniMax-M2.7 | 33/50 (66%) | 4.22s | 13,626 |
| MiniMax-M2.7-highspeed | 33/50 (66%) | 4.82s | 13,575 |

## Comparison vs Experiment 02 (26 cases)

| Model | 26-case | 50-case | Δ |
|---|---|---|---|
| M3 | 23/26 (88%) | 34/50 (68%) | **-20 pts** |
| M2.7-highspeed | 21/26 (81%) | 33/50 (66%) | **-15 pts** |
| M2.7 | 19/26 (73%) | 33/50 (66%) | -7 pts |

## Findings

1. **All three models converged.** On 50 cases, M3, M2.7, and M2.7-highspeed are within 2 percentage points of each other. On 26 cases, the gap was 15 points.

2. **M3's quality premium disappeared.** A 2pp gain for 58% more tokens is a bad value prop. On the 26-case suite, M3's 15pp gain might have justified the cost. On the 50-case suite, it doesn't.

3. **M2.7-highspeed tied M2.7 on quality, was actually slower.** The "highspeed" label is now misleading — it's no longer faster than regular M2.7, and isn't better either. It might just be retired.

4. **M3 still has the fastest latency on this run (2.11s).** That's interesting — the bigger model was the fastest. Latency ordering has been unstable across runs (variance is large).

5. **All three are hitting a similar ceiling.** When three distinct models tie at 66-68%, they're probably hitting a shared weakness — the eval itself. Either the cases are still too easy, or the models genuinely plateau on this kind of task.

## What this changes

- **The M2.7 sweet-spot story is back** — but for a different reason than Experiment 01. Now it's not "M2.7 is as good as M3, cheaper." It's "M3 is barely better than M2.7, at 58% more cost."
- **The M3 premium is now a real cost-benefit question** — a PM shipping AI features has to decide if a 2pp quality gain is worth 58% more tokens
- **For high-stakes use cases** (medical-advice adjacent, legal, etc.), even a 2pp quality gain might be worth it — context-dependent

## PM lesson

**The hardest eval you've run is the one most likely to show you don't have an eval hard enough.**

In Experiment 02 I had a clear winner (M3) and a confident story. In Experiment 03 the winner dissolved into a 2pp tie. Both findings are true at the same time. The right PM move is to keep raising the eval bar until the model rankings stop changing — and accept that you're never quite there.

## Next experiments

- Add ~20 cases specifically targeting the cases all three models failed (shared failure modes)
- Try a non-MiniMax model for an external comparison
- Variance experiments (N=3) before publishing any ranking
- Cost-weighted scoring: penalize the 58% token premium when computing a "value" score
