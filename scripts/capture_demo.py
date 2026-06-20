"""Capture a screenshot of the running Streamlit app for the README.

It builds the index, asks a sample question, waits for the local model's
answer, and saves a full-page screenshot showing a real conversation.

Usage (with the app running on http://localhost:8501):
    python scripts/capture_demo.py
"""

from pathlib import Path

from playwright.sync_api import sync_playwright

URL = "http://localhost:8501"
OUT = Path(__file__).resolve().parent.parent / "docs" / "demo.png"
QUESTION = "What is agent orchestration and when do we need a multi-agent system?"


def main() -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1280, "height": 1000})
        page.goto(URL, wait_until="networkidle")
        page.wait_for_timeout(3000)

        # Build / load the index first.
        page.get_by_role("button", name="Build / Load").click()
        # Wait for the indexing spinner to finish.
        page.wait_for_timeout(8000)

        # Ask a question in the chat input.
        chat = page.get_by_placeholder("Ask a question about your notes...")
        chat.click()
        chat.fill(QUESTION)
        chat.press("Enter")

        # Wait for the local LLM to generate the answer (can take a while).
        try:
            page.wait_for_selector(
                'div[data-testid="stChatMessage"]', timeout=120000
            )
        except Exception:  # noqa: BLE001
            pass
        # Give the model time to finish streaming the full answer.
        page.wait_for_timeout(20000)

        page.screenshot(path=str(OUT), full_page=True)
        browser.close()
    print(f"Saved screenshot to {OUT}")


if __name__ == "__main__":
    main()
