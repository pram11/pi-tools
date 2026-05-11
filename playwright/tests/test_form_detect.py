"""Tests for form field auto-detection."""

import json
import pytest
from playwright.sync_api import sync_playwright

FORM_HTML = """
<!DOCTYPE html>
<html><body>
<form id="login">
  <input type="text" name="username" placeholder="User" />
  <input type="password" name="password" />
  <textarea name="bio" rows="3"></textarea>
  <select name="role"><option>admin</option><option>user</option></select>
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


def test_detect_input_fields(page):
    from main import detect_form_fields
    fields = detect_form_fields(page)
    texts = [f["type"] for f in fields]
    assert "text" in texts
    assert "password" in texts


def test_detect_textarea(page):
    from main import detect_form_fields
    fields = detect_form_fields(page)
    names = [f["name"] for f in fields]
    assert "bio" in names
    types = [f["tag"] for f in fields]
    assert "textarea" in types


def test_detect_select(page):
    from main import detect_form_fields
    fields = detect_form_fields(page)
    names = [f["name"] for f in fields]
    assert "role" in names
    tags = [f["tag"] for f in fields]
    assert "select" in tags


def test_excludes_submit(page):
    from main import detect_form_fields
    fields = detect_form_fields(page)
    types = [f["type"] for f in fields]
    assert "submit" not in types


def test_field_count(page):
    from main import detect_form_fields
    fields = detect_form_fields(page)
    # username, password, bio, role = 4 (submit excluded)
    assert len(fields) == 4


def test_output_json_format(page):
    from main import detect_form_fields
    fields = detect_form_fields(page)
    raw = json.dumps(fields)
    parsed = json.loads(raw)
    assert all("tag" in f and "name" in f and "type" in f for f in parsed)
