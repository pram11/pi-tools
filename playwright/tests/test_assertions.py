"""Tests for Phase 5 assertions: expect-text, expect-visible, expect-url."""

import pytest
from playwright.sync_api import sync_playwright
from main import assert_text, assert_visible, assert_url


@pytest.fixture
def page():
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        p = browser.new_page()
        yield p
        browser.close()


class TestAssertText:
    """expect-text: verify text content of a selector."""

    def test_text_exists(self, page):
        page.set_content("<div id='x'>hello</div>")
        assert_text(page, "#x", "hello")  # should not raise

    def test_text_mismatch_raises(self, page):
        page.set_content("<div id='x'>hello</div>")
        with pytest.raises(AssertionError, match="expect-text"):
            assert_text(page, "#x", "goodbye")

    def test_text_partial(self, page):
        page.set_content("<div id='x'>hello world</div>")
        assert_text(page, "#x", "world")  # partial match OK

    def test_text_missing_selector_raises(self, page):
        page.set_content("<div>hi</div>")
        with pytest.raises(AssertionError, match="expect-text"):
            assert_text(page, "#missing", "hello")


class TestAssertVisible:
    """expect-visible: verify element is visible."""

    def test_visible_element(self, page):
        page.set_content("<div id='x'>hi</div>")
        assert_visible(page, "#x")

    def test_hidden_element_raises(self, page):
        page.set_content("<div id='x' style='display:none'>hi</div>")
        with pytest.raises(AssertionError, match="expect-visible"):
            assert_visible(page, "#x")

    def test_missing_selector_raises(self, page):
        page.set_content("<div>hi</div>")
        with pytest.raises(AssertionError, match="expect-visible"):
            assert_visible(page, "#nope")


class TestAssertUrl:
    """expect-url: verify page URL matches pattern."""

    def test_url_exact(self, page):
        page.goto("data:text/html,<h1>test</h1>")
        assert_url(page, page.url)

    def test_url_contains(self, page):
        page.goto("data:text/html,<h1>test</h1>")
        assert_url(page, "data:text/html")

    def test_url_mismatch_raises(self, page):
        page.goto("data:text/html,<h1>test</h1>")
        with pytest.raises(AssertionError, match="expect-url"):
            assert_url(page, "https://example.com")
