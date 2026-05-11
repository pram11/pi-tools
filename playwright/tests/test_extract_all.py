"""Tests for repeatable / recursive extraction (Phase 4)."""

import json
import pytest
from playwright.sync_api import sync_playwright

REPEAT_HTML = """
<!DOCTYPE html>
<html><body>
<div class="cards">
  <div class="card" data-id="1">
    <h2 class="title">Card A</h2>
    <span class="price">$10</span>
  </div>
  <div class="card" data-id="2">
    <h2 class="title">Card B</h2>
    <span class="price">$20</span>
  </div>
  <div class="card" data-id="3">
    <h2 class="title">Card C</h2>
    <span class="price">$30</span>
  </div>
</div>

<ul id="list">
  <li>First</li>
  <li>Second</li>
  <li>Third</li>
  <li>Fourth</li>
</ul>
</body></html>
"""


@pytest.fixture
def page():
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        p = browser.new_page()
        p.set_content(REPEAT_HTML)
        yield p
        browser.close()


# ── extract_all: simple repeat ──────────────────────────────────

def test_extract_all_text(page):
    from main import extract_all
    items = extract_all(page, ".card", ".title")
    assert items == ["Card A", "Card B", "Card C"]


def test_extract_all_count(page):
    from main import extract_all
    items = extract_all(page, "#list", "li")
    assert len(items) == 4


def test_extract_all_nth(page):
    """nth=0 → first element only, nth=2 → third."""
    from main import extract_all
    assert extract_all(page, "#list", "li", nth=0) == ["First"]
    assert extract_all(page, "#list", "li", nth=2) == ["Third"]


def test_extract_all_nth_out_of_range(page):
    from main import extract_all
    assert extract_all(page, "#list", "li", nth=10) == []


# ── extract_all: recursive (nested) ─────────────────────────────

def test_recursive_extract(page):
    """Extract multiple sub-fields per parent item."""
    from main import extract_all
    items = extract_all(page, ".card", {".title": "title", ".price": "price"})
    assert len(items) == 3
    assert items[0] == {"title": "Card A", "price": "$10"}
    assert items[1] == {"title": "Card B", "price": "$20"}
    assert items[2]["price"] == "$30"


def test_recursive_extract_missing_field(page):
    """Missing sub-selector → empty string."""
    from main import extract_all
    items = extract_all(page, ".card", {".title": "title", ".nonexistent": "missing"})
    assert items[0] == {"title": "Card A", "missing": ""}


# ── CLI action ──────────────────────────────────────────────────

def test_cli_extract_all_simple(capsys):
    import main, argparse
    args = argparse.Namespace(
        selector=".card", value=".title", url="data:text/html," + REPEAT_HTML,
        timeout=30000, retries=1, nth=None
    )
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        page = browser.new_page()
        page.set_content(REPEAT_HTML)
        main.action_extract_all(page, args)
        browser.close()
    captured = capsys.readouterr()
    parsed = json.loads(captured.out.strip())
    assert parsed == ["Card A", "Card B", "Card C"]


def test_cli_extract_all_recursive(capsys):
    import main, argparse
    # value = JSON map of sub-selectors
    args = argparse.Namespace(
        selector=".card",
        value=json.dumps({".title": "title", ".price": "price"}),
        url="data:text/html," + REPEAT_HTML,
        timeout=30000, retries=1, nth=None
    )
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        page = browser.new_page()
        page.set_content(REPEAT_HTML)
        main.action_extract_all(page, args)
        browser.close()
    captured = capsys.readouterr()
    parsed = json.loads(captured.out.strip())
    assert len(parsed) == 3
    assert parsed[0] == {"title": "Card A", "price": "$10"}


def test_cli_extract_all_nth(capsys):
    import main, argparse
    args = argparse.Namespace(
        selector="#list", value="li", url="data:text/html," + REPEAT_HTML,
        timeout=30000, retries=1, nth=1
    )
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        page = browser.new_page()
        page.set_content(REPEAT_HTML)
        main.action_extract_all(page, args)
        browser.close()
    captured = capsys.readouterr()
    parsed = json.loads(captured.out.strip())
    assert parsed == ["Second"]
