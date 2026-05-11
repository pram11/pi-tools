"""Tests for Phase 5: Wait-for-conditions (network idle, element state, HTTP status)."""

import pytest
from playwright.sync_api import sync_playwright
from main import wait_network_idle, wait_element_state, wait_http_status


@pytest.fixture
def page():
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        p = browser.new_page()
        yield p
        browser.close()


class TestWaitNetworkIdle:
    """wait_network_idle: block until no network requests for X ms."""

    def test_network_idle_resolves(self, page):
        # Simple page with no network activity after load
        page.goto("data:text/html,<h1>idle</h1>")
        result = wait_network_idle(page, idle_timeout=1000)
        assert result is True

    def test_network_idle_with_delayed_resource(self, page):
        # Page with inline script simulating delayed fetch
        page.set_content("""
            <html>
            <body>
                <h1>test</h1>
                <script>
                    setTimeout(() => {
                        fetch('data:text/plain,ok').then(r => r.text());
                    }, 100);
                </script>
            </body>
            </html>
        """)
        result = wait_network_idle(page, idle_timeout=500)
        assert result is True


class TestWaitElementState:
    """wait_element_state: block until element reaches specified state."""

    def test_wait_visible(self, page):
        page.set_content("<h1>test</h1>")
        result = wait_element_state(page, "h1", "visible")
        assert result is True

    def test_wait_hidden(self, page):
        page.set_content("<h1 style='display:none'>test</h1>")
        result = wait_element_state(page, "h1", "hidden")
        assert result is True

    def test_wait_attached(self, page):
        page.set_content("<div id='x'>hi</div>")
        result = wait_element_state(page, "#x", "attached")
        assert result is True

    def test_wait_detached(self, page):
        page.set_content("<h1>test</h1>")
        result = wait_element_state(page, "#missing", "detached", timeout=1000)
        assert result is True

    def test_wait_attached_raises_on_timeout(self, page):
        page.set_content("<h1>test</h1>")
        with pytest.raises(Exception, match="Timeout"):
            wait_element_state(page, "#nope", "attached", timeout=1000)


class TestWaitHttpStatus:
    """wait_http_status: block until response matches expected status code."""

    def test_status_200(self, page):
        # Use route.fulfill to generate a real HTTP response event
        page.route("**/api", lambda route: route.fulfill(status=200, body="ok"))
        result = wait_http_status(page, 200, url="http://localhost/api", timeout=3000)
        assert result is True

    def test_status_mismatch_raises(self, page):
        page.set_content("<h1>ok</h1>")
        with pytest.raises(Exception, match="wait-http-status|status"):
            wait_http_status(page, 404, timeout=2000)
