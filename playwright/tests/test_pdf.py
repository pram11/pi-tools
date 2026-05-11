"""Tests for PDF generation from page (Phase 4)."""

import json
import os
import pytest
from playwright.sync_api import sync_playwright

PAGE_HTML = """
<!DOCTYPE html>
<html><body>
<h1>Invoice #1234</h1>
<p>Total: $99.99</p>
<table>
  <tr><th>Item</th><th>Qty</th></tr>
  <tr><td>Widget</td><td>3</td></tr>
  <tr><td>Gadget</td><td>1</td></tr>
</table>
</body></html>
"""


@pytest.fixture
def page():
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        p = browser.new_page()
        p.set_content(PAGE_HTML)
        yield p
        browser.close()


def test_generate_pdf_returns_bytes(page, tmp_path):
    from main import generate_pdf
    output = tmp_path / "out.pdf"
    result = generate_pdf(page, str(output))
    assert isinstance(result, str)
    assert os.path.exists(result)
    size = os.path.getsize(result)
    assert size > 0


def test_generate_pdf_file_extension(page, tmp_path):
    from main import generate_pdf
    # Explicit .pdf extension
    output = tmp_path / "invoice.pdf"
    result = generate_pdf(page, str(output))
    assert result.endswith(".pdf")


def test_generate_pdf_default_extension(page, tmp_path):
    from main import generate_pdf
    # No extension → auto-append .pdf
    output = tmp_path / "receipt"
    result = generate_pdf(page, str(output))
    assert result.endswith(".pdf")
    assert os.path.exists(result)


def test_generate_pdf_format_option(page, tmp_path):
    from main import generate_pdf
    output = tmp_path / "opt.pdf"
    result = generate_pdf(page, str(output), format="A4")
    assert os.path.exists(result)
    assert os.path.getsize(result) > 0


def test_generate_pdf_print_background(page, tmp_path):
    from main import generate_pdf
    output = tmp_path / "bg.pdf"
    result = generate_pdf(page, str(output), print_background=True)
    assert os.path.exists(result)


def test_generate_pdf_margin_options(page, tmp_path):
    from main import generate_pdf
    output = tmp_path / "margin.pdf"
    result = generate_pdf(page, str(output), margin={"top": "1cm", "left": "1cm"})
    assert os.path.exists(result)


def test_generate_pdf_page_range(page, tmp_path):
    from main import generate_pdf
    output = tmp_path / "range.pdf"
    # single-page document, range="1"
    result = generate_pdf(page, str(output), page_range={"from": 0, "to": 0})
    assert os.path.exists(result)


def test_generate_pdf_scale(page, tmp_path):
    from main import generate_pdf
    output = tmp_path / "scale.pdf"
    result = generate_pdf(page, str(output), scale=0.8)
    assert os.path.exists(result)


def test_generate_pdf_outside_browser(page, tmp_path):
    """pdf generates with default options."""
    from main import generate_pdf
    output = tmp_path / "outside.pdf"
    result = generate_pdf(page, str(output))
    assert os.path.exists(result)


def test_cli_pdf_action(capsys, tmp_path):
    import main, argparse
    output = tmp_path / "cli.pdf"
    args = argparse.Namespace(
        output=str(output),
        url="data:text/html," + PAGE_HTML,
        timeout=30000,
        retries=1,
    )
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()
        page.set_content(PAGE_HTML)
        main.action_pdf(page, args)
        browser.close()
    captured = capsys.readouterr()
    assert "pdf" in captured.out.lower()
    assert os.path.exists(str(output))
