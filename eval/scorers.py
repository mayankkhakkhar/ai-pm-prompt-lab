"""Scorer functions — one per `scorer:` value in the YAML.

Each scorer receives the model's clean output and the YAML `expected` dict.
Returns (passed: bool, detail: str). The runner prints `detail` next to the
case so you can see *why* something passed or failed.

To add a new scorer:
  1. Write a function with the signature
     `fn(output: str, expected: dict, **kwargs) -> tuple[bool, str]`
  2. Add it to the SCORERS dict
  3. Reference it from a YAML case via `scorer: your_name`

YAML `expected` shape:
  expected:
    type: <scorer-name>      # optional, mirrors scorer field for self-doc
    value: <the main thing>  # what to check against
    ...                        # e.g. tolerance, criteria, etc.
"""
import json
import re
from typing import Any, Callable

from eval.parser import extract_json, strip_thinking


def exact_match(output: str, expected: dict) -> tuple[bool, str]:
    """Case-insensitive whole-string match against expected.value."""
    got = output.strip().lower()
    want = str(expected["value"]).strip().lower()
    passed = got == want
    return passed, f"output={got[:60]!r}"


def contains(output: str, expected: dict) -> tuple[bool, str]:
    """Case-insensitive substring match against expected.value."""
    got = output.strip().lower()
    want = str(expected["value"]).strip().lower()
    passed = want in got
    return passed, f"looking for {want!r} in {got[:60]!r}"


def regex_match(output: str, expected: dict) -> tuple[bool, str]:
    """Find a regex match anywhere in the output."""
    pattern = str(expected["value"])
    match = re.search(pattern, output.strip())
    if match:
        return True, f"matched={match.group(0)!r}"
    return False, f"no match for pattern {pattern!r}"


def word_count(output: str, expected: dict) -> tuple[bool, str]:
    """Count whitespace-separated words, allow +/- tolerance."""
    target = int(expected["value"])
    tolerance = int(expected.get("tolerance", 0))
    actual = len(output.strip().split())
    passed = abs(actual - target) <= tolerance
    return passed, f"got {actual} words, expected {target} (+/-{tolerance})"


def bullet_count(output: str, expected: dict) -> tuple[bool, str]:
    """Count lines that look like bullets (-, *, •, 1., 2.)."""
    target = int(expected["value"])
    tolerance = int(expected.get("tolerance", 0))
    bullets = [
        line for line in output.splitlines()
        if re.match(r"^\s*([-*•]\s|\d+[.)]\s)", line)
    ]
    actual = len(bullets)
    passed = abs(actual - target) <= tolerance
    return passed, f"got {actual} bullets, expected {target} (+/-{tolerance})"


def json_valid(output: str, expected: dict) -> tuple[bool, str]:
    """Parse JSON from the output and check required keys are present."""
    raw = extract_json(output)
    if raw is None:
        return False, f"no JSON object found in output: {output[:60]!r}"
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        return False, f"JSON parse error: {e}"
    required = expected.get("required_keys", [])
    missing = [k for k in required if k not in data]
    if missing:
        return False, f"missing keys: {missing}, got: {list(data.keys())}"
    return True, f"valid JSON with keys {list(data.keys())}"


def llm_judge(output: str, expected: dict, judge_client, model: str) -> tuple[bool, str]:
    """Use another LLM call to judge qualitative criteria. Costs an extra call.

    The judge prompt asks for PASS/FAIL on the first line, then one short
    sentence of reasoning. Temperature is forced to 0 for judgment stability.

    We parse defensively:
      - Strip thinking tokens (M2.7 reasons before answering)
      - Find PASS or FAIL anywhere in the cleaned text (not just line 1)
      - FAIL takes precedence if both appear (e.g. "not a PASS, it's a FAIL")
      - Extract whatever comes after the verdict as the explanation

    Retries up to 2 times if the judge model returns empty — M2.7
    occasionally spends its full token budget on thinking and emits
    nothing visible after stripping.
    """
    criteria = expected.get("criteria", [])
    rubric = "\n".join(f"- {c}" for c in criteria)

    prompt = (
        "You are evaluating an AI response against a rubric.\n\n"
        f"Response to evaluate:\n\"\"\"\n{output}\n\"\"\"\n\n"
        f"Criteria (the response must satisfy ALL of these):\n{rubric}\n\n"
        "Reply with EXACTLY two lines:\n"
        "Line 1: PASS or FAIL\n"
        "Line 2: One short sentence explaining why.\n"
    )

    last_error = ""
    for attempt in range(3):  # initial + 2 retries
        judgment = judge_client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
            max_tokens=300,
        )
        raw = judgment.choices[0].message.content
        text = strip_thinking(raw).strip()
        if text:
            break
        last_error = f"attempt {attempt + 1} returned empty"
    else:
        return False, f"judge: no response after 3 attempts ({last_error})"

    upper = text.upper()

    # FAIL wins if both appear
    has_pass = bool(re.search(r"\bPASS\b", upper))
    has_fail = bool(re.search(r"\bFAIL\b", upper))

    if has_fail and not has_pass:
        passed = False
        verdict = "FAIL"
    elif has_pass and not has_fail:
        passed = True
        verdict = "PASS"
    elif has_fail and has_pass:
        # Ambiguous — use whichever appears LAST (usually the verdict)
        last_pass = upper.rfind("PASS")
        last_fail = upper.rfind("FAIL")
        if last_fail > last_pass:
            passed = False
            verdict = "FAIL"
        else:
            passed = True
            verdict = "PASS"
    else:
        return False, f"judge: no PASS/FAIL in response: {text[:100]!r}"

    # Pull explanation: anything after the LAST verdict keyword
    last_idx = max(upper.rfind("PASS"), upper.rfind("FAIL"))
    explanation = text[last_idx:].lstrip("PASSFAILpassfail \t:-").strip()
    if not explanation:
        explanation = text[:100]

    return passed, f"judge ({verdict}): {explanation[:100]}"


SCORERS: dict[str, Callable] = {
    "exact": exact_match,
    "contains": contains,
    "regex": regex_match,
    "word_count": word_count,
    "bullet_count": bullet_count,
    "json_valid": json_valid,
    "llm_judge": llm_judge,
}


def get_scorer(name: str) -> Callable:
    if name not in SCORERS:
        raise ValueError(
            f"Unknown scorer: {name!r}. Known: {sorted(SCORERS.keys())}"
        )
    return SCORERS[name]