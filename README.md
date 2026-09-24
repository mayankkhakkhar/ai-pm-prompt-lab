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
   # Then edit .env and fill in your real keys
   ```
   - `MINIMAX_API_KEY` — get from the MiniMax platform dashboard
   - `GEMINI_API_KEY` — get from [Google AI Studio](https://aistudio.google.com/) (free tier is generous)

3. **Verify both providers work**
   ```bash
   python hello_minimax.py
   python hello_gemini.py
   ```
   If both print a 5-word greeting, your setup is correct.

## What's being built here

| Component | Purpose | Status |
|---|---|---|
| `hello_minimax.py` | Day 1 sanity check (MiniMax) | ✅ Day 1 |
| `hello_gemini.py` | Day 1 sanity check (Gemini) | ✅ Day 1 |
| Prompt playground | Swap prompts, compare outputs | 🚧 Days 3-4 |
| Eval harness | Run prompts against test sets | 🚧 Days 5-6 |
| Experiments | Temperature, system prompt, cost | 🚧 Days 7-8 |

## Folder structure (will grow)

```
ai-pm-prompt-lab/
├── hello_minimax.py        # First call — MiniMax
├── hello_gemini.py         # First call — Gemini
├── requirements.txt
├── .env.example
├── .gitignore
├── src/                    # Playground + eval logic (Days 3-6)
├── prompts/                # Prompt library (Days 4-5)
├── evals/                  # Test cases (Days 5-6)
└── experiments/            # Temperature, cost, etc. (Days 7-8)
```

## The 5 questions this lab trains you to answer

After Phase 1, you should be able to evaluate any LLM feature on:

1. **Latency** — p50, p95 of end-to-end response
2. **Cost** — per query, per user, monthly burn
3. **Quality** — pass rate on a representative set
4. **Variance** — does `temperature=0` give consistent outputs?
5. **Failure modes** — what's the worst output you've seen, and how do you detect it?

## License

MIT