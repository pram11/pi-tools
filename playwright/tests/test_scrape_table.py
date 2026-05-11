"""Tests for structured table scraping (Phase 4)."""

import json
import pytest
from playwright.sync_api import sync_playwright

TABLE_HTML = """
<!DOCTYPE html>
<html><body>
<table id="users">
  <thead>
    <tr><th>Name</th><th>Email</th><th>Role</th></tr>
  </thead>
  <tbody>
    <tr><td>Alice</td><td>alice@example.com</td><td>admin</td></tr>
    <tr><td>Bob</td><td>bob@example.com</td><td>user</td></tr>
    <tr><td>Carol</td><td>carol@example.com</td><td>user</td></tr>
  </tbody>
</table>

<table class="no-header">
  <tr><td>X</td><td>1</td></tr>
  <tr><td>Y</td><td>2</td></tr>
</table>
</body></html>
"""


@pytest.fixture
def page():
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        p = browser.new_page()
        p.set_content(TABLE_HTML)
        yield p
        browser.close()


def test_scrape_table_rows(page):
    from main import scrape_table
    rows = scrape_table(page, "#users")
    assert len(rows) == 3


def test_scrape_table_headers(page):
    from main import scrape_table
    rows = scrape_table(page, "#users")
    assert list(rows[0].keys()) == ["Name", "Email", "Role"]


def test_scrape_table_values(page):
    from main import scrape_table
    rows = scrape_table(page, "#users")
    assert rows[0] == {"Name": "Alice", "Email": "alice@example.com", "Role": "admin"}
    assert rows[1]["Name"] == "Bob"
    assert rows[2]["Email"] == "carol@example.com"


def test_scrape_table_no_header(page):
    """Table without thead → auto-generated col_1, col_2... keys."""
    from main import scrape_table
    rows = scrape_table(page, ".no-header")
    assert len(rows) == 2
    keys = list(rows[0].keys())
    assert keys == ["col_1", "col_2"]
    assert rows[0] == {"col_1": "X", "col_2": "1"}


def test_scrape_table_csv_format(page):
    from main import scrape_table
    csv_output = scrape_table(page, "#users", fmt="csv")
    lines = [l.strip() for l in csv_output.strip().splitlines()]
    assert len(lines) == 4  # header + 3 rows
    assert lines[0] == "Name,Email,Role"
    assert lines[1] == "Alice,alice@example.com,admin"


def test_scrape_table_empty(page):
    """Non-existent selector returns empty list."""
    from main import scrape_table
    rows = scrape_table(page, "#nonexistent")
    assert rows == []


def test_scrape_table_json_roundtrip(page):
    """Output is valid JSON serializable."""
    from main import scrape_table
    rows = scrape_table(page, "#users")
    raw = json.dumps(rows)
    parsed = json.loads(raw)
    assert len(parsed) == 3


def test_cli_scrape_action(capsys):
    """CLI action 'scrape' outputs JSON to stdout."""
    import main, argparse
    args = argparse.Namespace(
        selector="#users", value="json", url="data:text/html," + TABLE_HTML,
        timeout=30000, retries=1
    )
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()
        page.set_content(TABLE_HTML)
        main.action_scrape(page, args)
        browser.close()
    captured = capsys.readouterr()
    parsed = json.loads(captured.out.strip())
    assert len(parsed) == 3
    assert parsed[0]["Name"] == "Alice"
