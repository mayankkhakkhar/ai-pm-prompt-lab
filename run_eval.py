"""Run the eval harness against MiniMax and print pass rates.

Usage:
    python run_eval.py                    # run all cases
    python run_eval.py --case greeting_5_words   # run one case
    python run_eval.py --no-judge         # skip LLM-judge cases (faster, cheaper)
    python run_eval.py --evals path/to/set.yaml  # use a different eval set
    python run_eval.py --model MiniMax-M3          # test model (default: $MINIMAX_MODEL)
    python run_eval.py --judge-model MiniMax-M3    # judge model (default: same as test model)
"""
import argparse
import os
import time
from dataclasses import dataclass
from pathlib import Path

import yaml
from dotenv import load_dotenv
from openai import OpenAI

from eval.parser import strip_thinking
from eval.scorers import get_scorer


@dataclass
class CaseResult:
    id: str
    passed: bool
    detail: str
    latency: float
    tokens: int


def load_eval_set(path: Path) -> list[dict]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or "cases" not in data:
        raise ValueError(f"{path} must have a top-level `cases:` list")
    return data["cases"]


def call_model(client: OpenAI, model: str, case: dict, max_tokens: int = 800) -> tuple[str, float, int]:
    """Call MiniMax with the case's input. Returns (raw_output, latency, total_tokens)."""
    messages = []
    if system := case.get("input", {}).get("system"):
        messages.append({"role": "system", "content": system})
    user_msg = case.get("input", {}).get("user")
    if user_msg is None:
        raise ValueError(f"Case {case.get('id')!r} has no user message field")
    # Empty string is allowed (used by edge cases like edge_empty_input)
    messages.append({"role": "user", "content": user_msg})

    start = time.time()
    response = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=0.7,
        max_tokens=max_tokens,
    )
    latency = time.time() - start
    raw_output = response.choices[0].message.content
    tokens = response.usage.total_tokens
    return raw_output, latency, tokens


def run_case(client: OpenAI, model: str, case: dict, run_judge: bool, judge_model: str | None = None) -> CaseResult:
    scorer_name = case["scorer"]
    expected = case["expected"]
    # Judge uses judge_model if provided, else falls back to the test model.
    judge_to_use = judge_model or model

    # Skip judge cases if --no-judge
    if scorer_name == "llm_judge" and not run_judge:
        return CaseResult(
            id=case["id"], passed=False,
            detail="(skipped: LLM-judge, pass --judge to enable)",
            latency=0.0, tokens=0,
        )

    # Call the model with one retry on empty output (M2.7 sometimes
    # spends its full token budget on thinking and returns nothing visible).
    raw_output, latency, tokens = call_model(client, model, case)
    clean_output = strip_thinking(raw_output)
    retries = 0
    while not clean_output and retries < 1:
        raw_output, latency2, tokens2 = call_model(client, model, case)
        clean_output = strip_thinking(raw_output)
        latency += latency2
        tokens += tokens2
        retries += 1

    scorer = get_scorer(scorer_name)
    if scorer_name == "llm_judge":
        passed, detail = scorer(clean_output, expected, client, judge_to_use)
    else:
        passed, detail = scorer(clean_output, expected)

    return CaseResult(
        id=case["id"], passed=passed, detail=detail,
        latency=latency, tokens=tokens,
    )


def main():
    parser = argparse.ArgumentParser(description="Run the eval harness against MiniMax.")
    parser.add_argument("--evals", type=Path,
                        default=Path(__file__).parent / "evals" / "sample-set.yaml",
                        help="Path to eval set YAML")
    parser.add_argument("--case", type=str, default=None,
                        help="Run only this case id")
    parser.add_argument("--no-judge", action="store_true",
                        help="Skip LLM-judge cases (faster, no extra API calls)")
    parser.add_argument("--judge-model", type=str, default=None,
                        help="Model to use for LLM-judge calls (defaults to test model). "
                             "Use this to evaluate M2.7 with a stronger judge like MiniMax-M3.")
    parser.add_argument("--model", type=str, default=None,
                        help="Model to evaluate (defaults to $MINIMAX_MODEL or MiniMax-M2.7). "
                             "Used to test different models against the same eval set.")
    args = parser.parse_args()

    load_dotenv()
    api_key = os.environ.get("MINIMAX_API_KEY")
    if not api_key:
        raise SystemExit("MINIMAX_API_KEY not set — copy .env.example to .env and add your key.")

    base_url = os.environ.get("MINIMAX_BASE_URL", "https://api.minimax.io/v1")
    # CLI --model overrides env, which overrides the default
    model = args.model or os.environ.get("MINIMAX_MODEL", "MiniMax-M2.7")
    client = OpenAI(api_key=api_key, base_url=base_url)

    cases = load_eval_set(args.evals)
    if args.case:
        cases = [c for c in cases if c["id"] == args.case]
        if not cases:
            raise SystemExit(f"No case with id={args.case!r}")

    print(f"Loaded {len(cases)} case(s) from {args.evals.name}")
    print(f"Model: {model}")
    print(f"Judge model: {args.judge_model or model}")
    print(f"Judge calls: {'enabled' if not args.no_judge else 'disabled'}")
    print()
    print(f"{'STATUS':<6} {'CASE':<28} {'TIME':>6} {'TOKENS':>7}  DETAIL")
    print("-" * 100)

    results: list[CaseResult] = []
    for case in cases:
        result = run_case(client, model, case, run_judge=not args.no_judge, judge_model=args.judge_model)
        results.append(result)
        status = "PASS" if result.passed else "FAIL"
        time_str = f"{result.latency:.1f}s" if result.latency else "-"
        tok_str = f"{result.tokens}" if result.tokens else "-"
        # Truncate detail for the table; full detail shown in failures below
        detail = result.detail if not result.passed or len(result.detail) < 60 else result.detail[:57] + "..."
        print(f"[{status}] {result.id:<28} {time_str:>6} {tok_str:>7}  {detail}")

    # Summary
    passed = sum(1 for r in results if r.passed)
    total_real = sum(1 for r in results if r.tokens > 0)
    if total_real > 0:
        avg_latency = sum(r.latency for r in results if r.tokens > 0) / total_real
        total_tokens = sum(r.tokens for r in results)
    else:
        avg_latency = 0.0
        total_tokens = 0

    print()
    print("=" * 60)
    print(f"Pass rate:    {passed}/{len(results)} ({passed/len(results)*100:.0f}%)")
    if total_real > 0:
        print(f"Avg latency:  {avg_latency:.2f}s per case")
        print(f"Total tokens: {total_tokens:,}")
    print("=" * 60)

    # Show full details for failures
    failures = [r for r in results if not r.passed and r.tokens > 0]
    if failures:
        print()
        print("Failures (full detail):")
        for r in failures:
            print(f"  [{r.id}]")
            print(f"    {r.detail}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())