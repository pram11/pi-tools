"""Tests for lib.orchestrator."""

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest

# ── Unit tests (no browser) ──


def test_sanitize_html_strips_scripts():
    from lib.orchestrator import sanitize_html
    html = "<html><script>alert(1)</script><body><p>Hello</p></body></html>"
    result = sanitize_html(html)
    assert "<script>" not in result
    assert "<p>Hello</p>" in result


def test_sanitize_html_strips_styles():
    from lib.orchestrator import sanitize_html
    html = "<html><style>body{color:red}</style><body><p>Hello</p></body></html>"
    result = sanitize_html(html)
    assert "<style>" not in result
    assert "<p>Hello</p>" in result


def test_sanitize_html_strips_noscript():
    from lib.orchestrator import sanitize_html
    html = "<html><noscript>JS disabled</noscript><body><p>Hello</p></body></html>"
    result = sanitize_html(html)
    assert "<noscript>" not in result
    assert "<p>Hello</p>" in result


def test_html_to_markdown_basic():
    from lib.orchestrator import html_to_markdown
    html = "<h1>Title</h1><p>Body text.</p>"
    md = html_to_markdown(html)
    assert "# Title" in md
    assert "Body text" in md


def test_html_to_markdown_tables():
    from lib.orchestrator import html_to_markdown
    html = "<table><tr><th>A</th></tr><tr><td>1</td></tr></table>"
    md = html_to_markdown(html)
    assert "|" in md  # table format uses pipes


def test_extract_sub_region():
    from lib.orchestrator import extract_sub_region
    html = "<html><body><main id='content'><p>Target</p></main><div>Other</div></body></html>"
    result = extract_sub_region(html, "#content")
    assert "<p>Target</p>" in result
    assert "Other" not in result


def test_extract_sub_region_none_returns_full():
    from lib.orchestrator import extract_sub_region
    html = "<html><body><p>Full</p></body></html>"
    result = extract_sub_region(html, None)
    assert "<p>Full</p>" in result
