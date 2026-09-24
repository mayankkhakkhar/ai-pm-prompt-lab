# ai-pm-prompt-lab

Phase 1 of an 8-week AI PM sprint. A prompt playground + eval harness built to develop PM intuition about LLM behavior.

**This is a learning tool, not a product.** The goal is to build the muscle to evaluate any LLM feature a teammate ships.

## Quickstart

1. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set up API keys**
   ```bash
   cp .env.example .env
   # Then edit .env and fill in your real key
   ```
   - `MINIMAX_API_KEY` — get from the MiniMax platform dashboard

3. **Verify the API works**
   ```bash
   python hello_minimax.py
   ```
   If it prints a 5-word greeting, your setup is correct.

## What's being built here

| Component | Purpose | Status |
|---|---|---|
| `hello_minimax.py` | Day 1 sanity check | ✅ Day 1 |
| `show_request.py` | Inspect outgoing API request | ✅ Day 2 |
| Eval harness | Run prompts against test sets | ✅ Days 5-6 — 9/10 baseline |
| Prompt playground | Swap prompts, compare outputs | 🚧 Days 3-4 (next) |
| Experiments | Temperature, system prompt, cost | 🚧 Days 7-8 |

## Folder structure

```
ai-pm-prompt-lab/
├── hello_minimax.py        # First call to MiniMax (Day 1 sanity check)
├── show_request.py         # Print outgoing HTTP request, no API call
├── run_eval.py             # Eval harness runner (CLI)
├── requirements.txt
├── .env.example            # Template — copy to .env and add your key
├── .gitignore              # .env is gitignored
├── eval/                   # Scorers + parser (the harness logic)
│   ├── __init__.py
│   ├── parser.py           # Strip <think>...</think> from M2.7/M3 outputs
│   └── scorers.py          # 7 scorers: exact/contains/regex/word_count/bullet_count/json_valid/llm_judge
├── evals/                  # Eval sets (YAML)
│   └── sample-set.yaml     # 10 cases — format, knowledge, extraction, classification, qualitative
└── experiments/            # Temperature, cost, etc. (Days 7-8)
```

## Eval harness — current state

Run the eval set:

```bash
python run_eval.py                    # all cases
python run_eval.py --case meeting_summary   # one case
python run_eval.py --no-judge               # skip LLM-judge (faster)
python run_eval.py --judge-model MiniMax-M3 # use M3 as judge
```

**Baseline: 9/10 (90%)** with `MiniMax-M2.7` as test model and `MiniMax-M3` as judge.

| Result | Cases | Notes |
|---|---|---|
| ✅ 7/7 | All simple scorers (exact, contains, regex, word_count, bullet_count, json_valid) | M2.7 reliably follows format constraints and basic knowledge |
| ✅ 2/3 | LLM-judge cases (explain_concept, compare_options_balanced) | Pass with M3 as judge |
| ❌ 0/1 | meeting_summary | M2.7 misses the team-level design-review decision; M3 judge catches it honestly |

**Known finding:** M2.7 is unreliable as a judge of its own qualitative outputs — the thinking block consumes the token budget and returns empty. Fix: use `--judge-model MiniMax-M3`. This is a real production lesson: when you ship AI evals, "AI evaluates AI" needs a trustworthy evaluator, not the cheapest one.

## The 5 questions this lab trains you to answer

After Phase 1, you should be able to evaluate any LLM feature on:

1. **Latency** — p50, p95 of end-to-end response
2. **Cost** — per query, per user, monthly burn
3. **Quality** — pass rate on a representative set
4. **Variance** — does `temperature=0` give consistent outputs?
5. **Failure modes** — what's the worst output you've seen, and how do you detect it?

## License

MIT