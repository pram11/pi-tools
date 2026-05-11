"""Tests for Dialog/Alert interception (Phase 6)."""

import pytest
from playwright.sync_api import sync_playwright

DIALOG_HTML = """
<!DOCTYPE html>
<html><body>
<button id="alertBtn">Trigger Alert</button>
<button id="confirmBtn">Trigger Confirm</button>
<button id="promptBtn">Trigger Prompt</button>
<script>
  document.getElementById('alertBtn').onclick = () => alert('Alert message');
  document.getElementById('confirmBtn').onclick = () => {
    const r = confirm('Are you sure?');
    document.getElementById('result').textContent = r;
  };
  document.getElementById('promptBtn').onclick = () => {
    const r = prompt('Enter name:', 'default');
    document.getElementById('result').textContent = r || 'null';
  };
</script>
<span id="result"></span>
</body></html>
"""


@pytest.fixture
def page():
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        p = browser.new_page()
        p.set_content(DIALOG_HTML)
        yield p
        browser.close()


def test_intercept_alert_accept(page):
    """Intercept alert dialog and accept it."""
    from main import dialog_intercept

    messages = []
    dialog_intercept(page, mode="accept", callback=lambda d: messages.append(d.message))
    page.click("#alertBtn")
    assert messages == ["Alert message"]


def test_intercept_alert_dismiss(page):
    """Intercept alert dialog and dismiss it."""
    from main import dialog_intercept

    messages = []
    dialog_intercept(page, mode="dismiss", callback=lambda d: messages.append(d.message))
    page.click("#alertBtn")
    assert messages == ["Alert message"]


def test_intercept_confirm_accept(page):
    """Intercept confirm dialog and accept (return true)."""
    from main import dialog_intercept

    dialog_intercept(page, mode="accept")
    page.click("#confirmBtn")
    result = page.text_content("#result")
    assert result.strip() == "true"


def test_intercept_confirm_dismiss(page):
    """Intercept confirm dialog and dismiss (return false)."""
    from main import dialog_intercept

    dialog_intercept(page, mode="dismiss")
    page.click("#confirmBtn")
    result = page.text_content("#result")
    assert result.strip() == "false"


def test_intercept_prompt_accept_with_default(page):
    """Intercept prompt dialog, accept with default value."""
    from main import dialog_intercept

    dialog_intercept(page, mode="accept")
    page.click("#promptBtn")
    result = page.text_content("#result")
    assert result.strip() == "default"


def test_intercept_prompt_accept_with_value(page):
    """Intercept prompt dialog, accept with custom value."""
    from main import dialog_intercept

    dialog_intercept(page, mode="accept", prompt_text="John")
    page.click("#promptBtn")
    result = page.text_content("#result")
    assert result.strip() == "John"


def test_intercept_prompt_dismiss(page):
    """Intercept prompt dialog and dismiss (return null)."""
    from main import dialog_intercept

    dialog_intercept(page, mode="dismiss")
    page.click("#promptBtn")
    result = page.text_content("#result")
    assert result.strip() == "null"


def test_dialog_auto_accept(page):
    """Shorthand: auto-accept all dialogs on page."""
    from main import dialog_auto_accept

    messages = []
    dialog_auto_accept(page, callback=lambda d: messages.append(d.message))
    page.click("#alertBtn")
    assert messages == ["Alert message"]


def test_dialog_auto_dismiss(page):
    """Shorthand: auto-dismiss all dialogs on page."""
    from main import dialog_auto_dismiss

    dialog_auto_dismiss(page)
    page.click("#confirmBtn")
    result = page.text_content("#result")
    assert result.strip() == "false"


def test_dialog_types(page):
    """Read dialog type (alert, confirm, prompt)."""
    from main import dialog_intercept

    types = []
    dialog_intercept(page, mode="accept", callback=lambda d: types.append(d.type))
    page.click("#alertBtn")
    page.click("#confirmBtn")
    page.click("#promptBtn")
    assert types == ["alert", "confirm", "prompt"]


def test_multiple_alerts(page):
    """Handle multiple sequential alert dialogs."""
    from main import dialog_intercept

    messages = []
    dialog_intercept(page, mode="accept", callback=lambda d: messages.append(d.message))

    # Trigger alert twice via JS
    page.evaluate("alert('first'); alert('second');")
    assert messages == ["first", "second"]


def test_dialog_message(page):
    """Extract dialog message content."""
    from main import dialog_intercept

    messages = []
    dialog_intercept(page, mode="accept", callback=lambda d: messages.append(d.message))
    page.click("#alertBtn")
    assert messages[0] == "Alert message"


def test_action_dialog(page):
    """CLI action: dialog interception."""
    from main import action_dialog
    import argparse

    args = argparse.Namespace(
        action="dialog-accept",
        selector="#alertBtn",
        value=None,
        output=None,
        timeout=5000,
    )
    action_dialog(page, args)  # should not raise


def test_action_dialog_dismiss(page):
    """CLI action: dialog dismiss."""
    from main import action_dialog
    import argparse

    args = argparse.Namespace(
        action="dialog-dismiss",
        selector="#confirmBtn",
        value=None,
        output=None,
        timeout=5000,
    )
    action_dialog(page, args)


def test_action_dialog_prompt(page):
    """CLI action: dialog prompt with text."""
    from main import action_dialog
    import argparse

    args = argparse.Namespace(
        action="dialog-prompt",
        selector="#promptBtn",
        value="testName",
        output=None,
        timeout=5000,
    )
    action_dialog(page, args)
    result = page.text_content("#result")
    assert result.strip() == "testName"
