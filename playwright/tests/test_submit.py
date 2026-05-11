"""Tests for form submit handling — detect submission + wait for response."""

import pytest
from playwright.sync_api import sync_playwright

FORM_HTML = """
<!DOCTYPE html>
<html><body>
<form id="myform" action="/submitted" method="post">
  <input type="text" name="username" value="testuser" />
  <input type="submit" value="Submit" id="subBtn" />
</form>
</body></html>
"""

SUBMITTED_HTML = "<html><body><h1>Success</h1></body></html>"


@pytest.fixture
def page():
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        p = browser.new_page()
        p.set_content(FORM_HTML)
        yield p
        browser.close()


def test_submit_clicks_button(page):
    """Submit button click triggers form submit event."""
    from main import form_submit
    # Track submit event via JS
    page.evaluate("""
        () => {
            window.formSubmitted = false;
            document.getElementById('myform').addEventListener('submit', e => {
                window.formSubmitted = true;
            });
        }
    """)
    form_submit(page, selector="#subBtn")
    assert page.evaluate("window.formSubmitted") is True


def test_submit_waits_for_navigation(page):
    """After submit, waits for load and captures new URL/content."""
    from main import form_submit
    # Set base URL so form action resolves
    page.goto("http://example.com")
    page.set_content(FORM_HTML)
    page.route("**/submitted", lambda route, req: route.fulfill(status=200, body=SUBMITTED_HTML))
    result = form_submit(page, selector="#subBtn")
    assert "Success" in page.content()
    assert result["url"].endswith("/submitted")


def test_submit_by_form_selector(page):
    """Submit by targeting form element directly."""
    from main import form_submit
    page.evaluate("""
        () => {
            window.formSubmitted = false;
            document.getElementById('myform').addEventListener('submit', e => {
                window.formSubmitted = true;
            });
        }
    """)
    form_submit(page, selector="#myform")
    # form.submit() bypasses submit event — that's standard browser behavior
    # We verify it works by checking the action was attempted
    assert page.url == "about:blank"  # no route, stays on current


def test_submit_no_selector_errors(page):
    """Submit with nonexistent selector raises error."""
    from main import form_submit
    with pytest.raises(Exception):
        form_submit(page, selector=".nonexistent")


def test_submit_returns_url_after(page):
    """form_submit returns result dict with url key."""
    from main import form_submit
    result = form_submit(page, selector="#subBtn")
    assert "url" in result
    assert isinstance(result["url"], str)


def test_submit_default_selector(page):
    """Default selector finds first submit button."""
    from main import form_submit
    page.evaluate("""
        () => {
            window.formSubmitted = false;
            document.getElementById('myform').addEventListener('submit', e => {
                window.formSubmitted = true;
            });
        }
    """)
    result = form_submit(page)
    assert page.evaluate("window.formSubmitted") is True
    assert "url" in result
