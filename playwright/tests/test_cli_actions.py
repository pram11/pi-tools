"""Unit tests for CLI action dispatchers (Phase 7).

Tests individual action_* functions with isolated pages.
"""

import json
import os
import pytest
from playwright.sync_api import sync_playwright
from main import (
    action_navigate,
    action_click,
    action_type,
    action_extract,
    action_screenshot,
    action_wait,
    action_eval,
    action_scroll,
)


class FakeArgs:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


@pytest.fixture
def page():
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        p = browser.new_page()
        yield p
        browser.close()


class TestActionNavigate:
    """action_navigate: load URL via domcontentloaded."""

    def test_navigate_data_url(self, page, capsys):
        page.set_content("<h1>ok</h1>")
        action_navigate(
            page,
            FakeArgs(url="data:text/html,<h1>navigated</h1>", timeout=30000, retries=1),
        )
        assert page.url == "data:text/html,<h1>navigated</h1>"

    def test_navigate_output(self, page, capsys):
        action_navigate(
            page,
            FakeArgs(url="data:text/html,<h1>x</h1>", timeout=30000, retries=1),
        )
        out = capsys.readouterr().out
        assert "[navigate]" in out


class TestActionClick:
    """action_click: click selector."""

    def test_click_button(self, page):
        page.set_content(
            "<button id='b'>Go</button><script>document.getElementById('b').onclick=()=>document.body.textContent='clicked'</script>"
        )
        action_click(page, FakeArgs(selector="#b"))
        assert page.text_content("body") == "clicked"


class TestActionType:
    """action_type: fill input via --value."""

    def test_fill_input(self, page):
        page.set_content("<input id='q' type='text' />")
        action_type(page, FakeArgs(selector="#q", value="hello"))
        assert page.input_value("#q") == "hello"

    def test_fill_missing_selector_raises(self, page):
        page.set_content("<input id='q' />")
        page.set_default_timeout(1000)
        with pytest.raises(Exception):
            action_type(page, FakeArgs(selector="#missing", value="x"))


class TestActionExtract:
    """action_extract: text_content via --selector."""

    def test_extract_text(self, page, capsys):
        page.set_content("<div id='x'>hello world</div>")
        action_extract(page, FakeArgs(selector="#x"))
        assert "hello world" in capsys.readouterr().out

    def test_extract_missing(self, page, capsys):
        page.set_content("<div>hi</div>")
        page.set_default_timeout(1000)
        with pytest.raises(Exception):
            action_extract(page, FakeArgs(selector="#nope"))


class TestActionScreenshot:
    """action_screenshot: save PNG."""

    def test_screenshot_default(self, page, tmp_path, capsys):
        page.set_content("<h1>snap</h1>")
        out = str(tmp_path / "screenshot.png")
        action_screenshot(page, FakeArgs(output=out))
        assert os.path.exists(out)
        assert os.path.getsize(out) > 0

    def test_screenshot_custom_path(self, page, tmp_path):
        page.set_content("<h1>x</h1>")
        out = str(tmp_path / "custom.png")
        action_screenshot(page, FakeArgs(output=out))
        assert os.path.exists(out)


class TestActionWait:
    """action_wait: wait_for_selector."""

    def test_wait_existing(self, page):
        page.set_content("<div id='x'>hi</div>")
        action_wait(page, FakeArgs(selector="#x", value="5000"))

    def test_wait_missing_raises(self, page):
        page.set_content("<div>hi</div>")
        with pytest.raises(Exception):
            action_wait(page, FakeArgs(selector="#nope", value="1000"))


class TestActionEval:
    """action_eval: page.evaluate JS."""

    def test_eval_expression(self, page, capsys):
        page.set_content("<div>hi</div>")
        action_eval(page, FakeArgs(value="1 + 2"))
        assert "3" in capsys.readouterr().out

    def test_eval_document(self, page, capsys):
        page.set_content("<h1 id='t'>title</h1>")
        action_eval(page, FakeArgs(value="document.title"))
        out = capsys.readouterr().out
        assert json.loads(out) == ""


class TestActionScroll:
    """action_scroll: window.scrollTo."""

    def test_scroll_top(self, page):
        page.set_content("<div style='height:200vh'></div>")
        page.evaluate("window.scrollTo(0, 500)")
        action_scroll(page, FakeArgs(value="top"))
        assert page.evaluate("window.scrollY") == 0

    def test_scroll_bottom(self, page):
        page.set_content("<div style='height:200vh'></div>")
        action_scroll(page, FakeArgs(value="bottom"))
        pos = page.evaluate("window.scrollY")
        assert pos > 0

    def test_scroll_default_top(self, page):
        page.set_content("<div style='height:200vh'></div>")
        page.evaluate("window.scrollTo(0, 500)")
        action_scroll(page, FakeArgs(value=None))
        assert page.evaluate("window.scrollY") == 0
