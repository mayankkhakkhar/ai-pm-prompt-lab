# ai-pm-prompt-lab

**Phase 1 of an 8-week AI PM sprint.** An eval harness + prompt playground built to develop PM intuition about LLM behavior — what models actually do, not what their marketing pages claim.

Built by a product manager learning AI engineering from a builder's perspective. The goal isn't shipping a product; it's building the muscle to evaluate any LLM feature a teammate (or vendor) ships.

---

## What this repo contains

| Component | What it does | Try it |
|---|---|---|
| **Prompt playground** | Streamlit app — type one prompt, see 3 temperature variants side by side | `streamlit run playground.py` |
| **Eval harness** | 50 test cases (knowledge, format, extraction, classification, qualitative, **health-insurance**, edge cases), 7 scorer types, runs any model against the suite | `python run_eval.py --model MiniMax-M3 --judge-model MiniMax-M3` |
| **Experiments** | Real model comparisons, documented findings | [`experiments/`](./experiments/) |

![Playground showing 3 temperature variants of the same prompt](./docs/screenshots/playground-filled.png)

---

## Quickstart

```bash
git clone https://github.com/mayankkhakkhar/ai-pm-prompt-lab.git
cd ai-pm-prompt-lab
pip install -r requirements.txt

cp .env.example .env
# Edit .env and add your MiniMax API key

# Try the playground
streamlit run playground.py
# Opens http://localhost:8501

# Try the eval harness
python run_eval.py --model MiniMax-M2.7 --judge-model MiniMax-M3
```

---

## The prompt playground

A web UI where you type one prompt, pick a model and a token budget, and see 3 temperature variants run side by side.

![Empty playground](./docs/screenshots/playground-empty.png)

**What it teaches:** the same prompt produces visibly different outputs at temp=0.0 (deterministic), 0.7 (balanced), 1.0 (creative). PMs in AI products need this intuition before they can reason about model behavior.

**What it has:**
- Model picker (M2.7, M2.7-highspeed, M2.5, M2.5-highspeed, M2.1, M3)
- Max-output-tokens slider (default 800)
- Side-by-side comparison with latency + token count per variant
- Read-only output boxes so Streamlit can't cache stale state

**Try it:** `streamlit run playground.py`

---

## The eval harness

A CLI that runs a YAML-defined test suite against any model and prints pass rates.

```bash
python run_eval.py --model MiniMax-M2.7 --judge-model MiniMax-M3
```

**Output:**

```
STATUS CASE                           TIME  TOKENS  DETAIL
[PASS] greeting_5_words               3.2s      94  got 5 words, expected 5 (+/-0)
[PASS] capital_france                 1.2s      67  looking for 'paris' in 'paris'
[PASS] largest_planet                 1.5s      98  looking for 'jupiter' in 'jupiter'
[PASS] extract_email                  2.4s     167  matched='jane.smith@company.co.uk'
[PASS] sentiment_positive             1.3s      64  looking for 'positive' in 'positive'
[PASS] summarize_3_bullets            2.4s     188  got 3 bullets, expected 3 (+/-0)
[PASS] json_formatting                2.1s     122  valid JSON with keys ['name', 'age', 'role']
[PASS] explain_concept                1.9s     127  judge (PASS): The response is factually accurate...
[PASS] compare_options_balanced       6.3s     299  judge (PASS): The response covers pros and cons...
[PASS] meeting_summary                4.7s     380  judge (PASS): All criteria are satisfied...
... (16 more cases — health insurance, edge cases, variance variants) ...
[FAIL] hi_preauth_requirement         7.6s     342  judge (FAIL): response is cut off, didn't explain prior auth...
[FAIL] hi_preventive_care_coverage   13.0s     702  judge (FAIL): response is empty (thinking ate the budget)...
[FAIL] edge_contradictory_instructions   6.6s     351  judge (FAIL): wrote the essay anyway, ignored the "one sentence" rule...

Pass rate:    21/26 (81%)
Avg latency:  4.15s per case
Total tokens: 6,229
```

The failing cases are the interesting ones — they reveal real model weaknesses (token-budget starvation, constraint-overriding reasoning, missing specific facts like "180-day appeal window").

Full sample run: [`docs/sample-eval-output.txt`](./docs/sample-eval-output.txt)

### 7 scorer types

`exact`, `contains`, `regex`, `word_count`, `bullet_count`, `json_valid`, `llm_judge`

The `llm_judge` scorer is the interesting one — it makes a second API call to a judge model and asks it to evaluate against a rubric. Useful for qualitative tests like "is this explanation age-appropriate?"

### Test cases in `evals/sample-set.yaml` (50 total)

- **Format constraints** — word count, bullet count, JSON structure
- **Knowledge retrieval** — capital cities, planets
- **Extraction** — email (3 variants), phone, dollar amount, date, policy numbers
- **Classification** — sentiment (3 variants), urgency, intent
- **Qualitative (LLM-judge)** — explain concepts, compare options, summarize meetings
- **Health insurance (PM-flavored, 20 cases)** — deductibles, copay vs coinsurance, EOBs, denial reasons, formulary tiers, appeals, preventive care, HMO vs PPO, ER vs urgent care, generic vs brand, step therapy, coordination of benefits, No Surprises Act, HSA vs FSA, metal tiers, EOB line items, medical-advice safety
- **Variance variants (6 cases)** — same skill, different inputs (summarization, extraction, sentiment, JSON) to measure reliability
- **Edge cases (6 cases)** — empty input, contradictory instructions, very long input, one-word input, numbers-only input, prompt-injection attempt

### Flags

```
--model MiniMax-M3        # test model (defaults to $MINIMAX_MODEL)
--judge-model MiniMax-M3  # judge model (defaults to test model — usually bad)
--case meeting_summary    # run one case
--no-judge                # skip LLM-judge cases (faster, cheaper)
--evals path/to/set.yaml  # use a different eval set
```

---

## The experiments

Documented comparisons and findings in [`experiments/`](./experiments/).

| # | Title | Finding |
|---|---|---|
| 01 | [3-model eval comparison (10 cases)](./experiments/01-3-model-eval-comparison.md) | On an easy eval, all 3 models hit 100%. Doesn't tell you which to ship. |
| 02 | [3-model eval comparison (26 cases)](./experiments/02-3-model-eval-on-harder-suite.md) | On a hard eval, M3 (88%) > M2.7-highspeed (81%) > M2.7 (73%). M3 costs 49% more tokens. |
| 03 | [3-model eval comparison (50 cases)](./experiments/03-50-case-eval-the-ceiling.md) | On the hardest eval yet, all 3 models converge to 66-68%. M3's premium doesn't pencil out. |

---

## What we learned (the PM lessons)

These are findings from building this lab. Not opinions — measurements.

### 1. The judge matters more than you think

M2.7-as-judge was unreliable — it over-thinks and returns empty. Switching the judge to M3 unlocked 2 cases that had been failing. **Lesson:** in production, "AI evaluates AI" needs a trustworthy evaluator. Don't use the cheapest model for judging.

### 2. Model choice depends on task difficulty (revisit, don't trust a single eval)

On the easy 10-case suite, M2.7 hit the same 10/10 as M3 while using fewer tokens. On the harder 26-case suite (with PM-flavored health insurance cases), the ranking flipped: **M3 88% > M2.7-highspeed 81% > M2.7 73%**. **Lesson:** a single eval is a snapshot. The PM move is to run the same comparison against a *harder* suite before you commit to a model — and weight the harder numbers, because those are closer to real product traffic.

### 3. "Fast" models aren't free — but the tradeoff is more nuanced than the marketing

On the 10-case suite, M2.7-highspeed was the fastest but lost 2 points. On the 26-case suite, highspeed actually *beat* M2.7 (81% vs 73%) — less over-thinking on hard prompts gave more reliable answers. **Lesson:** "speed tier" pitches aren't always a quality cut. For harder prompts, sometimes the cheaper model with less reasoning is the better choice. Always measure.

### 4. Token budget = output completeness

M2.7 emits a `` block before answering. That reasoning eats into the token cap. At `max_tokens=300`, the visible answer often cuts off mid-sentence or returns empty. At 800, complete answers. **Lesson:** budget for AI products must include reasoning overhead — typically 60-70% of the cap is invisible to the user.

### 5. Eval scores have variance

M2.7 scored 21/26 on one run and 19/26 on the next — same eval, same model, same temperature. **Lesson:** never ship a "model X is better than Y" claim from one eval run. N=3 minimum for any conclusion worth publishing.

### 6. Prompts have ceilings

The `meeting_summary` case initially required M2.7 to extract 3+ action items, but it returned 2. Even after sharpening the system prompt, M2.7's reasoning rejected "the team decided to postpone X" as "a decision, not an action item." **Lesson:** reasoning models can over-rule surface instructions. Sometimes the right fix is a stronger model, not a better prompt.

### 7. Evals need to be hard to be useful

The original 10-case suite had all three models at or near 100%. It looked like a tie. Adding 10 health insurance cases and 6 edge/variance cases *broke the tie*: M3 pulled ahead, highspeed moved up, M2.7 dropped 27 points. **Lesson:** a 100%-passing eval is suspicious — it usually means the cases are too easy. The PM move is to add cases that *should* fail, then see which models actually handle them.

---

## Phase 2 (in progress): what RAG is, and what we'll build

> Roadmap primer — RAG code hasn't shipped yet. This section is the *what + why + how* before we write a line of Python.

### What RAG is, in one paragraph

**Retrieval-Augmented Generation.** Instead of asking a model to answer from its training data, you look up relevant chunks in a corpus first, then put those chunks into the prompt the model sees.

```
+----------+        +------------------+        +-----------+
|  query   | -----> |   retriever      | -----> | generator |
+----------+        |  (BM25/embeddings)|        |   (LLM)   |
                    +------------------+        +-----------+
                           |                          ^
                           v                          |
                     +-----------+              +-------------+
                     |  top-K    |              |  query +   |
                     |  chunks   |              |  chunks    |
                     | from      |              |  in prompt |
                     | corpus    |              +-------------+
                     +-----------+
```

Three pieces. The corpus is the "knowledge base." The retriever picks the relevant bits. The generator uses those bits to answer — with citations, in theory.

### Why PMs care

A RAG system is what most "AI products" actually are under the hood. Customer support chatbots, internal knowledge search, "ask the docs," most copilots. If you can build and evaluate one, you can talk to any vendor in this space without sounding like a tourist.

### Where RAG fits in the AI toolkit

The four ways to give a model "knowledge" — cheapest at the top, most powerful at the bottom:

| Approach | What you change | When it fits |
|---|---|---|
| **Prompt engineering** | Just the prompt | Behavior tweaks, format control, no new facts needed |
| **RAG** | Add a retrieval step + ground the prompt | Facts you want fresh, cite-able, or per-user |
| **Fine-tuning** | Update model weights | Style, format, behavior patterns — not new facts |
| **Pre-training** | Train from scratch | A research project; almost never a PM move |

Rule of thumb you'll hear over and over: **"RAG before fine-tuning for new knowledge, fine-tuning before pre-training for new behavior."** Worth knowing the order — vendors will skip steps in the pitch.

### Why PMs care (concrete benefits)

- **Grounds responses in a specific corpus.** The model's answer is tied to your docs, not its training mix. (This is the headline.)
- **Fetches up-to-date data.** The corpus isn't baked in at training time. Swap a doc and the next query reflects it.
- **Works in specialized domains** — legal, medical, financial — without retraining on those corpora.
- **Personalizes per user or per tenant.** Different customers can see different corpuses (their own contract, their own org's docs). Fine-tuning can't do this cleanly.
- **Cite-able.** You can show users which sources were used, and audit when the sources are wrong.
- **Cheaper than fine-tuning** for most "knowledge" use cases. Tune ≠ retrain ≠ fine-tune ≠ pretrain.
- **Failure modes you can debug.** "Bad answer" usually splits into (a) bad retrieval, (b) good retrieval + bad generation. Knowing which lets you fix the right thing.

### What we learned in Phase 1 that applies directly

- **Hard cases expose model differences.** A RAG eval that's "answer = doc text verbatim" won't tell you anything. The interesting failures are partial retrieval, retrieval-then-ignore, and confident hallucination despite a chunk being present.
- **Reasoning models spend tokens on thinking.** M2.7 emits `<think>` blocks before any visible output. If we put 8 chunks in the prompt, the model may chew through tokens deciding which to use *before* answering. Budget for that.
- **Token cost compounds.** A RAG prompt is `[system] + [N chunks] + [query]`. At 8 chunks × 400 tokens + 200 system + 80 query = ~3,500 input tokens *per query*. Cost is not optional in a RAG design.
- **LLM-as-judge works.** We already use it for the eval harness. We can grade RAG answers against gold Q&A pairs the same way.

### What we'll build (the actual plan)

A self-contained RAG over **this repo**:

| Piece | Choice | Why |
|---|---|---|
| **Corpus** | README.md + all of `experiments/*.md` + `evals/sample-set.yaml` | Self-contained, no licensing issues, the docs a learner actually reads |
| **Chunker** | Section-level on `.md` files, key-aware on YAML | Markdown has headers — use them. YAML by top-level keys. |
| **Retriever (v1)** | BM25 keyword search via `rank_bm25` | Zero external deps, no rate limits, instant. Lets us ship the *shape* first. |
| **Retriever (v2)** | MiniMax `embo-01` embeddings | Semantic match ("deductible" → "out-of-pocket max"). Different schema from OpenAI (`texts[]` + `type`, returns `vectors`). |
| **Generator** | MiniMax-M3 (the M3 from Phase 1) | We already know its failure modes. Don't introduce a new model at the same time as a new architecture. |
| **Eval** | Author ~20 gold Q&A pairs (e.g. "What scoring approach did Experiment 02 use?") and grade with the existing `llm_judge` scorer | No need to write a separate eval infrastructure — reuse. |
| **Retrieval eval** | Hit rate @ K = fraction of gold questions where the right chunk is in the top-K retrieved | We evaluate retrieval separately from generation. The PM move: when answer quality drops, first check if retrieval dropped. |

Target outcome: a single Python file `run_rag.py` that takes a question and returns `[answer, cited chunk IDs, retrieval latency, generation latency, total tokens]`.

### What RAG adds to the PM question set

After Phase 2, the questions the lab trains you to answer expand to:

1. **Retrieval quality** — does the right chunk surface in top-K?
2. **Faithfulness** — does the answer only use the retrieved chunks, or does the model pull in outside knowledge?
3. **Chunk strategy** — chunking by sentence / paragraph / section / document? Each has trade-offs (precision vs context).
4. **Failure attribution** — when an answer is wrong, was it retrieval or generation? (Both can fail; they need different fixes.)
5. **Cost at scale** — `embeddings + retriever + N-chunks-prompt + generation` per query × monthly queries = real number

### Challenges RAG doesn't solve for you

Worth knowing the failure modes before you ship:

- **Retrieval quality sets a ceiling on answer quality.** Garbage chunks in → garbage answer out, even from a great model. Retriever evaluation is not optional.
- **Latency compounds.** Embedding + vector lookup + LLM call = three sequential steps. Worst-case p95 can be 3-4× a plain LLM call.
- **Bias from the corpus.** RAG doesn't remove bias — it *imports* it from whatever you put in the corpus. Garbage in, garbage (confidently) out.
- **The two-system tuning problem.** Retrieval and generation each have their own knobs (chunk size, K, embedding model, temperature, prompt shape). Bad retrieval looks like bad generation from the user's perspective.
- **The model may ignore retrieved chunks** when it has high confidence in its own (possibly wrong) prior. Faithfulness is an evaluation, not a guarantee.

### Open questions we'll resolve when we build

These are the ones I don't have an answer for yet — finding out is the point:

- **BM25 vs embeddings, on our 60-doc corpus.** BM25 might actually win here. Embeddings shine on huge corpora; on a small domain corpus with section headers and consistent vocabulary, keyword match may be enough.
- **How chunk size affects answer quality.** We have no intuition yet for this corpus.
- **Whether the model will *ignore* the chunks** when it's confident in its own (wrong) answer. The Phase 1 prompt-injection edge case already hinted: M2.1 complied with injection even when an unrelated task was set up. With conflicting context, the model may favor its own beliefs.

I'll log findings in `experiments/04-rag-over-this-repo.md` once we run them.

---

## Repo structure

```
ai-pm-prompt-lab/
├── hello_minimax.py            # Day 1 sanity check
├── show_request.py             # Inspect outgoing HTTP request (no API call)
├── playground.py               # Streamlit prompt playground
├── run_eval.py                 # Eval harness CLI
├── eval/
│   ├── parser.py               # Strip <think>...</think> from model output
│   └── scorers.py              # 7 scorer implementations
├── evals/
│   └── sample-set.yaml         # 50 eval cases (knowledge, format, extraction, qualitative, health insurance, edge)
├── experiments/
│   ├── 01-3-model-eval-comparison.md          # 10-case baseline
│   ├── 02-3-model-eval-on-harder-suite.md     # 26-case follow-up — hard evals change the ranking
│   ├── 03-50-case-eval-the-ceiling.md         # 50-case — all models converge when eval is hard enough
│   └── 04-rag-over-this-repo.md   (Phase 2, pending)
├── docs/
│   ├── screenshots/            # For the README
│   ├── eval-50-*.txt           # Frozen 50-case eval runs (6 models)
│   └── sample-eval-output.txt  # Frozen eval run output
├── scripts/
│   └── capture_screenshots.py  # Playwright-based screenshot script
├── requirements.txt
├── .env.example
├── .gitignore                  # .env is gitignored
└── LICENSE                     # MIT
```

---

## The 5 questions this lab trains you to answer

After Phase 1, you should be able to evaluate any LLM feature on:

1. **Latency** — p50, p95 of end-to-end response
2. **Cost** — per query, per user, monthly burn
3. **Quality** — pass rate on a representative test set
4. **Variance** — does `temperature=0` give consistent outputs?
5. **Failure modes** — what's the worst output you've seen, and how do you detect it?

---

## Status

| Component | Status |
|---|---|
| Eval harness (50 cases, 7 scorers) | ✅ done |
| Prompt playground (model picker, temp sweep, max_tokens) | ✅ done |
| 3-model comparison (10-case baseline + 26-case follow-up + 50-case ceiling) | ✅ done |
| PM-flavored health insurance cases (20 total) | ✅ done |
| Token-budget + prompt-fix experiments | ✅ done |
| RAG primer (concepts + build plan, in this README) | ✅ done |
| RAG implementation (`run_rag.py`, retrieval eval) | 🚧 next |
| Variance experiments (N=3 per model) | ⏳ later |
| AI Agents (Phase 3) | ⏳ later |

---

## License

MIT — see [`LICENSE`](./LICENSE).
