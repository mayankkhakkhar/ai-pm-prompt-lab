"""Helpers for parsing model output.

The main thing: strip <think>...</think> blocks that MiniMax-M2.7/M3 emit
before the final answer. Without this, eval scoring would match against
the model's reasoning, not its actual response.
"""
import re

THINK_RE = re.compile(r"<think>.*?</think>\s*", re.DOTALL)


def strip_thinking(text: str) -> str:
    """Remove <think>...</think> blocks from a model's output."""
    return THINK_RE.sub("", text).strip()


def extract_json(text: str) -> str | None:
    """Pull the first JSON object out of a string, if one exists.

    Models often wrap JSON in prose ("Here is the JSON: {...}"). For
    json_valid scoring, we want to find the object, not require the
    entire output to be JSON.
    """
    match = re.search(r"\{.*\}", text, re.DOTALL)
    return match.group(0) if match else None