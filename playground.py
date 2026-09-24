"""Prompt playground — side-by-side temperature comparison.

Run with:
    streamlit run playground.py
    # then open http://localhost:8501 in your browser

What it does:
    Type one prompt, click "Run all 3 variants." See how the same prompt
    produces different outputs at temperature 0.0 / 0.7 / 1.0 — same model,
    same input, different sampling. Latency and token cost per variant.

Why temperature matters for a PM:
    - temp=0   → same answer every run (deterministic, safe for production)
    - temp=0.7 → balanced — some creativity, mostly reliable (most apps live here)
    - temp=1.0 → high variance — useful for brainstorming, dangerous for shipping
"""
import os
import time

import streamlit as st
from dotenv import load_dotenv
from openai import OpenAI

from eval.parser import strip_thinking


VARIANTS = [
    ("A — temp=0.0 (deterministic)", 0.0),
    ("B — temp=0.7 (balanced)",       0.7),
    ("C — temp=1.0 (creative)",       1.0),
]

AVAILABLE_MODELS = [
    "MiniMax-M2.7",
    "MiniMax-M2.7-highspeed",
    "MiniMax-M2.5",
    "MiniMax-M2.5-highspeed",
    "MiniMax-M2.1",
    "MiniMax-M3",
]

DEFAULT_SYSTEM = "You are a helpful assistant."
DEFAULT_USER = "Explain the difference between SQL JOIN types to a junior engineer."


def get_client_and_model() -> tuple[OpenAI | None, str]:
    """Load .env once and return (client, model)."""
    load_dotenv()
    api_key = os.environ.get("MINIMAX_API_KEY")
    if not api_key:
        return None, ""
    client = OpenAI(
        api_key=api_key,
        base_url=os.environ.get("MINIMAX_BASE_URL", "https://api.minimax.io/v1"),
    )
    model = os.environ.get("MINIMAX_MODEL", "MiniMax-M2.7")
    return client, model


def call_variant(client: OpenAI, model: str, messages: list[dict], temperature: float, max_tokens: int) -> tuple[str, float, int, str | None]:
    """Run one variant. Returns (clean_output, latency_s, tokens, error_or_None)."""
    try:
        start = time.time()
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        raw = response.choices[0].message.content
        clean = strip_thinking(raw)
        latency = time.time() - start
        tokens = response.usage.total_tokens
        return clean, latency, tokens, None
    except Exception as e:
        return "", 0.0, 0, str(e)


def main() -> None:
    st.set_page_config(page_title="Prompt playground", layout="wide")
    st.title("Prompt playground")
    st.caption("Same prompt, three temperatures, side by side.")

    client, default_model = get_client_and_model()
    if not client:
        st.error("MINIMAX_API_KEY not set — copy .env.example to .env and add your key.")
        st.stop()

    # Model picker — defaults to whatever's in .env. Lets you swap models
    # without changing the env (and without affecting the eval harness).
    model = st.selectbox(
        "Model",
        options=AVAILABLE_MODELS,
        index=AVAILABLE_MODELS.index(default_model) if default_model in AVAILABLE_MODELS else 0,
        help="Default is from .env (MINIMAX_MODEL). highspeed variants use less reasoning budget.",
    )

    max_tokens = st.slider(
        "Max output tokens per variant",
        min_value=100,
        max_value=2000,
        value=800,
        step=100,
        help="Cap on the model's response length. Higher = more complete answers, more cost, more latency.",
    )

    # ── Input form ───────────────────────────────────────────────────────────
    with st.form("prompt_form"):
        system_prompt = st.text_area(
            "System prompt (optional)",
            value=DEFAULT_SYSTEM,
            height=80,
            help="Sets the model's role / instructions. Leave blank to skip.",
        )
        user_prompt = st.text_area(
            "User prompt",
            value=DEFAULT_USER,
            height=100,
        )
        run = st.form_submit_button("Run all 3 variants")

    if not run:
        return

    if not user_prompt.strip():
        st.error("Enter a user prompt first.")
        st.stop()

    messages: list[dict] = []
    if system_prompt.strip():
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": user_prompt})

    # ── Run all variants ─────────────────────────────────────────────────────
    progress = st.progress(0.0, "Starting...")
    results: list[tuple[str, float, str, float, int, str | None]] = []
    for i, (label, temp) in enumerate(VARIANTS, 1):
        progress.progress((i - 1) / len(VARIANTS), f"Running {label}...")
        out, lat, tok, err = call_variant(client, model, messages, temp, max_tokens)
        results.append((label, temp, out, lat, tok, err))
    progress.progress(1.0, "Done.")

    # ── Display side by side ─────────────────────────────────────────────────
    cols = st.columns(3)
    for col, (label, temp, out, lat, tok, err) in zip(cols, results):
        with col:
            st.subheader(label)
            if err:
                st.error(err)
            elif not out:
                st.warning("Empty response after stripping thinking tokens.")
            else:
                # text_area keeps the original UI. Tall enough height to
                # hold ~50 lines without scrolling; longer outputs scroll inside.
                st.text_area(
                    "Output",
                    value=out,
                    height=600,
                    key=f"out_{temp}",
                    label_visibility="collapsed",
                )
                st.caption(f"Latency: {lat:.2f}s  |  Tokens: {tok}")


if __name__ == "__main__":
    main()
