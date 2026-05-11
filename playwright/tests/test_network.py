"""Tests for network interception (Phase 4)."""

import json
import pytest
from playwright.sync_api import sync_playwright


@pytest.fixture
def server():
    """Simple HTTP server for API endpoint testing."""
    import threading
    from http.server import HTTPServer, BaseHTTPRequestHandler

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            if self.path == "/api/data":
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("X-Custom", "hello")
                self.end_headers()
                self.wfile.write(json.dumps([{"id": 1, "name": "test"}]).encode())
            elif self.path == "/api/error":
                self.send_response(500)
                self.send_header("Content-Type", "text/plain")
                self.end_headers()
                self.wfile.write(b"server error")
            elif self.path == "/api/text":
                self.send_response(200)
                self.send_header("Content-Type", "text/plain")
                self.end_headers()
                self.wfile.write(b"hello world")
            else:
                self.send_response(404)
                self.end_headers()

        def log_message(self, *args):
            pass  # suppress logs

    srv = HTTPServer(("127.0.0.1", 0), Handler)
    port = srv.server_address[1]
    t = threading.Thread(target=srv.serve_forever, daemon=True)
    t.start()
    yield port
    srv.shutdown()


def test_capture_all_responses(server):
    """capture_network returns all responses with url, status, headers, body."""
    from main import capture_network
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()
        url = f"http://127.0.0.1:{server}/api/data"
        responses = capture_network(page, url)
        browser.close()

    api = [r for r in responses if "/api/data" in r["url"]]
    assert len(api) >= 1
    resp = api[0]
    assert resp["status"] == 200
    assert resp["headers"]["content-type"] == "application/json"
    assert resp["headers"]["x-custom"] == "hello"
    body = json.loads(resp["body"])
    assert body == [{"id": 1, "name": "test"}]


def test_capture_error_response(server):
    """Capture 500 response correctly."""
    from main import capture_network
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()
        url = f"http://127.0.0.1:{server}/api/error"
        responses = capture_network(page, url)
        browser.close()

    err = [r for r in responses if "/api/error" in r["url"]]
    assert len(err) >= 1
    assert err[0]["status"] == 500
    assert err[0]["body"] == "server error"


def test_capture_filter_by_status(server):
    """filter_status returns only matching status codes."""
    from main import capture_network
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()
        url = f"http://127.0.0.1:{server}/api/data"
        responses = capture_network(page, url)
        browser.close()

    ok_only = [r for r in responses if r["status"] == 200]
    assert len(ok_only) >= 1


def test_capture_text_body(server):
    """Non-JSON body captured as string."""
    from main import capture_network
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()
        url = f"http://127.0.0.1:{server}/api/text"
        responses = capture_network(page, url)
        browser.close()

    txt = [r for r in responses if "/api/text" in r["url"]]
    assert len(txt) >= 1
    assert txt[0]["body"] == "hello world"


def test_cli_network_action(server, capsys):
    """CLI action 'network' outputs captured responses as JSON."""
    import main, argparse
    args = argparse.Namespace(
        url=f"http://127.0.0.1:{server}/api/data",
        timeout=30000,
        retries=1,
        selector=None,
        value=None,
        output=None,
        nth=None,
    )
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()
        main.action_network(page, args, browser=browser, context=context)
        browser.close()
    captured = capsys.readouterr()
    result = json.loads(captured.out.strip())
    assert isinstance(result, list)
    api = [r for r in result if "/api/data" in r["url"]]
    assert len(api) >= 1
    assert api[0]["status"] == 200
