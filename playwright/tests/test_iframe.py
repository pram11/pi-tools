"""Tests for iframe context switching (Phase 6)."""

import json
import pytest
from playwright.sync_api import sync_playwright

IFRAME_HTML = """
<!DOCTYPE html>
<html><body>
<h1 id="main">Main Page</h1>

<iframe id="frame1" srcdoc="
  <html><body>
    <h2 id='frame1-title'>Frame 1 Title</h2>
    <input id='frame1-input' value='initial' />
    <button id='frame1-btn'>Frame 1 Button</button>
    <p id='frame1-para'>Frame 1 Paragraph</p>
  </body></html>
"></iframe>

<iframe id="frame2" srcdoc="
  <html><body>
    <h2 id='frame2-title'>Frame 2 Title</h2>
    <div class='data'>Frame 2 Data</div>
  </body></html>
"></iframe>

<iframe id="nested-frame" srcdoc="
  <html><body>
    <h2 id='nested-title'>Nested Frame</h2>
    <div id='nest-target'></div>
  </body></html>
"></iframe>
</body></html>
"""


@pytest.fixture
def page():
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        p = browser.new_page()
        p.set_content(IFRAME_HTML)
        yield p
        browser.close()


# ── RED: Tests that fail (no implementation yet) ──────────────


def test_iframe_list(page):
    """List all iframes on page with their content_frame info."""
    from main import iframe_list
    frames = iframe_list(page)
    assert len(frames) == 3
    assert any(f["name"] == "frame1" for f in frames)


def test_iframe_query(page):
    """One-liner query: read text inside iframe without manual context switch."""
    from main import iframe_query
    result = iframe_query(page, "#frame1", "#frame1-title")
    assert result == "Frame 1 Title"


def test_iframe_query_missing(page):
    """Return None when inner selector not found inside iframe."""
    from main import iframe_query
    result = iframe_query(page, "#frame1", "#nonexistent")
    assert result is None


def test_iframe_query_missing_iframe(page):
    """Return None when iframe selector not found."""
    from main import iframe_query
    result = iframe_query(page, "#missing-frame", "#something")
    assert result is None


def test_iframe_click(page):
    """Click element inside iframe."""
    from main import iframe_click, iframe_query
    iframe_click(page, "#frame1", "#frame1-btn")
    # Verify button still exists (no handler, just verify no error)
    result = iframe_query(page, "#frame1", "#frame1-btn")
    assert result == "Frame 1 Button"


def test_iframe_fill(page):
    """Fill input inside iframe."""
    from main import iframe_fill
    iframe_fill(page, "#frame1", "#frame1-input", "new value")
    # verify via frame_locator
    fl = page.frame_locator("#frame1")
    val = fl.locator("#frame1-input").input_value(timeout=5000)
    assert val == "new value"


def test_iframe_enter_exit(page):
    """Enter iframe context, operate, exit back to main."""
    from main import iframe_enter, iframe_exit
    iframe_enter(page, "#frame1")
    # Verify active frame_locator is set
    assert hasattr(page, "_active_fl")
    iframe_exit(page)
    assert page._active_fl is None  # type: ignore[attr-defined]
    # Back in main frame
    main_text = page.text_content("#main")
    assert main_text == "Main Page"


def test_iframe_nested(page):
    """Navigate into nested iframe (iframe within iframe)."""
    from main import iframe_enter, iframe_exit
    iframe_enter(page, "#nested-frame")
    outer_fl = page._active_fl  # type: ignore[attr-defined]
    # Create inner iframe with createElement + srcdoc (avoids escaping issues)
    outer_fl.locator("#nest-target").evaluate("""
        el => {
            const iframe = document.createElement('iframe');
            iframe.srcdoc = '<html><body><span id="deep-text">Deep Inside</span></body></html>';
            el.appendChild(iframe);
        }
    """)
    page.wait_for_timeout(500)
    # Chained frame_locator: outer_fl → nested iframe
    inner_fl = outer_fl.frame_locator("iframe")
    page._active_fl = inner_fl  # type: ignore[attr-defined]
    text = inner_fl.locator("#deep-text").inner_text(timeout=5000)
    assert text == "Deep Inside"
    iframe_exit(page)
    iframe_exit(page)


def test_iframe_extract(page):
    """Extract text from element inside iframe."""
    from main import iframe_extract
    result = iframe_extract(page, "#frame1", "#frame1-para")
    assert result == "Frame 1 Paragraph"


def test_iframe_multi_extract(page):
    """Extract multiple elements from iframe."""
    from main import iframe_multi_extract
    results = iframe_multi_extract(page, "#frame1", "h2, p")
    assert "Frame 1 Title" in results
    assert "Frame 1 Paragraph" in results


def test_action_iframe_query(page):
    """CLI action: iframe-query."""
    from main import action_iframe
    import argparse
    args = argparse.Namespace(
        action="iframe-query",
        selector="#frame1",
        value="#frame1-title",
        output=None
    )
    action_iframe(page, args)


def test_action_iframe_fill(page):
    """CLI action: iframe-fill."""
    from main import action_iframe
    import argparse
    args = argparse.Namespace(
        action="iframe-fill",
        selector="#frame1",
        value="#frame1-input",
        output="test value"
    )
    action_iframe(page, args)


def test_action_iframe_click(page):
    """CLI action: iframe-click."""
    from main import action_iframe
    import argparse
    args = argparse.Namespace(
        action="iframe-click",
        selector="#frame1",
        value="#frame1-btn",
        output=None
    )
    action_iframe(page, args)


def test_action_iframe_list(page):
    """CLI action: iframe-list."""
    from main import action_iframe
    import argparse
    args = argparse.Namespace(
        action="iframe-list",
        selector=None,
        value=None,
        output=None
    )
    action_iframe(page, args)


def test_action_iframe_extract(page):
    """CLI action: iframe-extract."""
    from main import action_iframe
    import argparse
    args = argparse.Namespace(
        action="iframe-extract",
        selector="#frame2",
        value=".data",
        output=None
    )
    action_iframe(page, args)
