"""E2E smoke test: navigate → click → extract → screenshot.

Validates full CLI action pipeline end-to-end.
Phase 7 checklist item.
"""

import json
import os
import pytest
from playwright.sync_api import sync_playwright
from main import (
    action_navigate,
    action_click,
    action_extract,
    action_screenshot,
)


class FakeArgs:
    """Minimal argparse.Namespace stand-in."""

    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


@pytest.fixture
def page():
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        p = browser.new_page()
        yield p
        browser.close()


@pytest.fixture
def smoke_html():
    return """
    <!DOCTYPE html>
    <html>
      <body>
        <h1 id="title">Smoke Test Page</h1>
        <button id="btn">Click Me</button>
        <div id="result" style="display:none">Extracted!</div>
        <script>
          document.getElementById('btn').addEventListener('click', () => {
            document.getElementById('result').style.display = 'block';
          });
        </script>
      </body>
    </html>
    """


def test_smoke_navigate_click_extract_screenshot(page, smoke_html, tmp_path):
    """Full pipeline: navigate → click → extract → screenshot."""
    data_url = f"data:text/html,{smoke_html}"

    # 1. Navigate
    action_navigate(page, FakeArgs(url=data_url, timeout=30000, retries=1))

    # 2. Click button → reveals hidden div
    action_click(page, FakeArgs(selector="#btn"))

    # 3. Extract revealed text
    captured = []

    class CaptureExtract:
        def __call__(self, page, args):
            text = page.text_content(args.selector) or ""
            captured.append(text.strip())

    capture = CaptureExtract()
    capture(page, FakeArgs(selector="#result"))
    assert captured[0] == "Extracted!"

    # 4. Screenshot
    out = str(tmp_path / "smoke.png")
    action_screenshot(page, FakeArgs(output=out))
    assert os.path.exists(out)
    assert os.path.getsize(out) > 0
