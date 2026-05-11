"""Tests for multi-step form (wizard) automation."""

import pytest
from playwright.sync_api import sync_playwright

# Wizard: step1 → step2 → submit
# No form action to prevent navigation — pure JS wizard
WIZARD_HTML = """
<!DOCTYPE html>
<html><body>
<div id="wizard">
  <div id="step1">
    <h2>Step 1: Account</h2>
    <input type="text" name="email" placeholder="Email" />
    <input type="password" name="password" />
    <button type="button" class="next" onclick="showStep(2)">Next</button>
  </div>
  <div id="step2" style="display:none">
    <h2>Step 2: Profile</h2>
    <input type="text" name="firstName" placeholder="First Name" />
    <input type="text" name="lastName" placeholder="Last Name" />
    <select name="country">
      <option value="">Select</option>
      <option value="us">United States</option>
      <option value="uk">United Kingdom</option>
    </select>
    <button type="button" class="back" onclick="showStep(1)">Back</button>
    <button type="button" class="next" onclick="showStep(3)">Next</button>
  </div>
  <div id="step3" style="display:none">
    <h2>Step 3: Confirm</h2>
    <p id="summary"></p>
    <button type="button" id="submitBtn" onclick="document.getElementById('result').style.display='block'">Create Account</button>
  </div>
  <div id="result" style="display:none"><h1>Account Created</h1></div>
</div>
<script>
function showStep(n) {
  document.querySelectorAll('[id^=step]').forEach(el => el.style.display='none');
  document.getElementById('step' + n).style.display = 'block';
}
</script>
</body></html>
"""


@pytest.fixture
def page():
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        p = browser.new_page()
        p.set_content(WIZARD_HTML)
        yield p
        browser.close()


def test_wizard_fill_all_steps(page):
    """Fill wizard across 3 steps, submit, verify result."""
    from main import wizard_fill
    steps = [
        {"fields": {"email": "a@b.com", "password": "secret123"}},
        {"fields": {"firstName": "John", "lastName": "Doe", "country": "us"}},
        {"fields": {}, "submit": True, "next": "#submitBtn"},
    ]
    result = wizard_fill(page, steps)
    assert result["steps_filled"] == 3
    assert result["submitted"] is True
    assert page.input_value("[name=email]") == "a@b.com"
    assert page.input_value("[name=firstName]") == "John"


def test_wizard_detect_current_step(page):
    """Detect which step is visible."""
    assert page.is_visible("#step1") is True
    assert page.is_visible("#step2") is False
    assert page.is_visible("#step3") is False


def test_wizard_default_next_selector(page):
    """Default .next button advances steps."""
    from main import wizard_fill
    steps = [
        {"fields": {"email": "x@y.com", "password": "p"}},
        {"fields": {"firstName": "J", "lastName": "D", "country": "us"}},
    ]
    result = wizard_fill(page, steps)
    assert result["steps_filled"] == 2
    assert page.is_visible("#step3") is True


def test_wizard_custom_next_selector(page):
    """Custom next button selector works."""
    from main import wizard_fill
    steps = [
        {"fields": {"email": "c@d.com", "password": "p"}},
    ]
    result = wizard_fill(page, steps, next_selector="button.next")
    assert result["steps_filled"] == 1
    assert page.is_visible("#step2") is True


def test_wizard_submit_step(page):
    """Last step with submit=True clicks submit button."""
    from main import wizard_fill
    # Navigate to step 3 first via wizard_fill
    wizard_fill(page, [
        {"fields": {"email": "e@t.com", "password": "p"}},
        {"fields": {"firstName": "F", "lastName": "L", "country": "us"}},
    ])
    assert page.is_visible("#step3") is True
    result = wizard_fill(page, [{"fields": {}, "submit": True, "next": "#submitBtn"}])
    assert result["submitted"] is True
    assert page.is_visible("#result") is True


def test_wizard_empty_steps(page):
    """Empty steps list returns 0 steps filled."""
    from main import wizard_fill
    result = wizard_fill(page, [])
    assert result["steps_filled"] == 0


def test_wizard_partial_fill(page):
    """Fill only some fields per step, skip others."""
    from main import wizard_fill
    steps = [
        {"fields": {"email": "partial@test.com"}},
    ]
    result = wizard_fill(page, steps)
    assert result["steps_filled"] == 1
    assert page.input_value("[name=email]") == "partial@test.com"
    assert page.input_value("[name=password]") == ""


def test_wizard_step_with_custom_next(page):
    """Override next selector per step."""
    from main import wizard_fill
    steps = [
        {"fields": {"email": "e@e.com", "password": "p"}, "next": "#step1 button.next"},
    ]
    result = wizard_fill(page, steps)
    assert result["steps_filled"] == 1
    assert page.is_visible("#step2") is True


def test_wizard_skips_fields_on_submit_step(page):
    """Submit step with no fields just clicks submit."""
    from main import wizard_fill
    result = wizard_fill(page, [{"fields": {}, "submit": True, "next": "button.next"}])
    assert result["submitted"] is True
    assert result["steps_filled"] == 1
