"""Capture a screenshot of the running Streamlit app for the README.

Usage (with the app running on http://localhost:8501):
    python scripts/capture_demo.py
"""

from pathlib import Path

from playwright.sync_api import sync_playwright

URL = "http://localhost:8501"
OUT = Path(__file__).resolve().parent.parent / "docs" / "demo.png"


def main() -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1280, "height": 900})
        page.goto(URL, wait_until="networkidle")
        # Give Streamlit a moment to finish rendering widgets.
        page.wait_for_timeout(3000)
        page.screenshot(path=str(OUT), full_page=True)
        browser.close()
    print(f"Saved screenshot to {OUT}")


if __name__ == "__main__":
    main()
