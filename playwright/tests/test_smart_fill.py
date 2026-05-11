"""Tests for smart form fill — map field names to values from dict."""

import pytest
from playwright.sync_api import sync_playwright

FORM_HTML = """
<!DOCTYPE html>
<html><body>
<form id="login">
  <input type="text" name="username" placeholder="User" />
  <input type="password" name="password" />
  <textarea name="bio" rows="3"></textarea>
  <select name="role"><option>admin</option><option>user</option><option>guest</option></select>
  <input type="checkbox" name="agree" />
  <input type="submit" value="Go" />
</form>
</body></html>
"""


@pytest.fixture
def page():
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        p = browser.new_page()
        p.set_content(FORM_HTML)
        yield p
        browser.close()


def test_fill_text_input(page):
    from main import smart_fill
    filled = smart_fill(page, {"username": "alice"})
    assert "username" in filled
    assert page.input_value("[name=username]") == "alice"


def test_fill_password_input(page):
    from main import smart_fill
    filled = smart_fill(page, {"password": "s3cret"})
    assert "password" in filled
    assert page.input_value("[name=password]") == "s3cret"


def test_fill_textarea(page):
    from main import smart_fill
    filled = smart_fill(page, {"bio": "Hello world"})
    assert "bio" in filled
    assert page.input_value("[name=bio]") == "Hello world"


def test_fill_select(page):
    from main import smart_fill
    filled = smart_fill(page, {"role": "admin"})
    assert "role" in filled
    assert page.eval_on_selector("[name=role]", "el => el.value") == "admin"


def test_fill_checkbox(page):
    from main import smart_fill
    filled = smart_fill(page, {"agree": True})
    assert "agree" in filled
    assert page.eval_on_selector("[name=agree]", "el => el.checked") is True


def test_fill_checkbox_false(page):
    from main import smart_fill
    page.check("[name=agree]")  # check first
    assert page.eval_on_selector("[name=agree]", "el => el.checked") is True
    filled = smart_fill(page, {"agree": False})
    assert "agree" in filled
    assert page.eval_on_selector("[name=agree]", "el => el.checked") is False


def test_ignore_unknown_field(page):
    from main import smart_fill
    filled = smart_fill(page, {"username": "bob", "nonexistent": "x"})
    assert "username" in filled
    assert "nonexistent" not in filled


def test_fill_multiple_fields(page):
    from main import smart_fill
    filled = smart_fill(page, {"username": "carol", "password": "pass123", "bio": "dev"})
    assert "username" in filled
    assert "password" in filled
    assert "bio" in filled
    assert page.input_value("[name=username]") == "carol"
    assert page.input_value("[name=password]") == "pass123"
    assert page.input_value("[name=bio]") == "dev"


def test_empty_dict_no_op(page):
    from main import smart_fill
    filled = smart_fill(page, {})
    assert filled == []
