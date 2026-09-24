"""Capture screenshots of the playground for the README.

Run with:
    python scripts/capture_screenshots.py

Output:
    docs/screenshots/playground-empty.png
    docs/screenshots/playground-filled.png

Requires:
    streamlit run playground.py  (must be running on localhost:8501)
    playwright + chromium installed
"""
import sys
import time
from pathlib import Path

from playwright.sync_api import sync_playwright


SCREENSHOTS_DIR = Path(__file__).parent.parent / "docs" / "screenshots"


def capture():
    SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1400, "height": 900})
        page = context.new_page()

        # 1. Empty playground (default state)
        print("Capturing empty playground...")
        page.goto("http://localhost:8501", wait_until="networkidle", timeout=30000)
        time.sleep(3)  # let streamlit finish initial render
        page.screenshot(path=str(SCREENSHOTS_DIR / "playground-empty.png"), full_page=True)
        print(f"  -> playground-empty.png")

        # 2. Filled playground — type a new prompt, click Run, capture outputs
        print("Capturing filled playground (typing prompt + clicking Run)...")

        # Use a short prompt — long prompts cause M2.7 to burn the budget on thinking
        # and return empty (the max_tokens lesson). Short prompts produce visible output.
        user_prompt_textarea = page.locator('textarea').nth(1)
        user_prompt_textarea.click()
        user_prompt_textarea.fill("Explain compound interest in 3 sentences for a 10-year-old.")

        # Click the Run button
        run_button = page.get_by_role("button", name="Run all 3 variants")
        run_button.click()

        # Poll for completion: wait until all 3 output textareas appear
        # (they only render after the API calls complete)
        print("  Waiting for 3 variants to complete...")
        for _ in range(60):  # up to 60s
            time.sleep(1)
            count = page.locator('textarea').count()
            # 1 model select + 1 system prompt + 1 user prompt + 3 outputs = 6
            if count >= 6:
                break
        else:
            print("  Warning: timed out waiting for outputs")

        # Give an extra moment for render
        time.sleep(2)

        page.screenshot(path=str(SCREENSHOTS_DIR / "playground-filled.png"), full_page=True)
        print(f"  -> playground-filled.png")

        browser.close()
        print("Done.")


if __name__ == "__main__":
    try:
        capture()
    except Exception as e:
        print(f"Failed: {e}", file=sys.stderr)
        sys.exit(1)
