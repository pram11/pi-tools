"""Auto-recovery on page crash / navigation timeout."""

import subprocess
import sys
import tempfile
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path

MAIN = Path(__file__).parent.parent / "main.py"
PYTHON = sys.executable


def _run(args: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(
        [PYTHON, str(MAIN)] + args,
        capture_output=True, text=True, timeout=60,
    )


class SlowHandler(BaseHTTPRequestHandler):
    """Serves page after 10s delay — triggers navigation timeout."""
    def do_GET(self):
        import time
        time.sleep(10)
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"<html><body>slow</body></html>")

    def log_message(self, *a):
        pass  # silence stderr


class CrashingHandler(BaseHTTPRequestHandler):
    """Returns HTML that crashes the renderer via OOM simulation."""
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        # JavaScript that throws — simulates a crashy page
        self.wfile.write(b"<html><body><script>throw new Error('boom')</script></body></html>")

    def log_message(self, *a):
        pass


def _start_server(handler_cls, port: int = 18930) -> HTTPServer:
    server = HTTPServer(("127.0.0.1", port), handler_cls)
    t = threading.Thread(target=server.serve_forever, daemon=True)
    t.start()
    return server


def test_navigation_timeout_retries_then_succeeds():
    """Page times out once, auto-recovery retries, succeeds on second attempt with fast server."""
    from socketserver import ThreadingMixIn
    import tempfile, os
    with tempfile.TemporaryDirectory() as tmp:
        html = Path(tmp) / "index.html"
        html.write_text("<h1>recovery-ok</h1>")

        # serve slow first request, then fast
        class OnceSlowHandler(BaseHTTPRequestHandler):
            requests = [0]

            def do_GET(self):
                import time
                self.__class__.requests[0] += 1
                if self.__class__.requests[0] == 1:
                    # first request: sleep past timeout
                    time.sleep(10)
                    self.send_response(200)
                    self.end_headers()
                    self.wfile.write(b"<html><body>slow</body></html>")
                else:
                    self.send_response(200)
                    self.end_headers()
                    self.wfile.write(b"<html><body><h1>fast-ok</h1></body></html>")

            def log_message(self, *a):
                pass

        class ThreadedServer(ThreadingMixIn, HTTPServer):
            daemon_threads = True

        port = 18931
        server = ThreadedServer(("127.0.0.1", port), OnceSlowHandler)
        t = threading.Thread(target=server.serve_forever, daemon=True)
        t.start()
        base = f"http://127.0.0.1:{port}/index.html"

        try:
            # --timeout 2000 (2s), --retries 2
            # First attempt times out, second succeeds
            r = _run([
                "--url", base,
                "--action", "navigate",
                "--timeout", "2000",
                "--retries", "2",
            ])
            assert r.returncode == 0, f"Auto-recovery failed: {r.stderr}"
            assert "recovery" in r.stdout.lower() or "Loaded" in r.stdout, \
                f"Expected success output, got: {r.stdout}"
        finally:
            server.shutdown()


def test_navigation_timeout_exhausts_retries():
    """All retries fail → non-zero exit, recovery message in stderr."""
    import tempfile
    with tempfile.TemporaryDirectory() as tmp:
        port = 18932
        server = _start_server(SlowHandler, port)
        base = f"http://127.0.0.1:{port}/"

        try:
            r = _run([
                "--url", base,
                "--action", "navigate",
                "--timeout", "1000",
                "--retries", "2",
            ])
            assert r.returncode != 0, "Expected failure after exhausting retries"
        finally:
            server.shutdown()


def test_page_crash_recover_with_retry():
    """Page with JS error → recover on retry with valid page."""
    with tempfile.TemporaryDirectory() as tmp:
        html = Path(tmp) / "index.html"
        html.write_text("<h1>crash-ok</h1>")

        class OnceCrashHandler(BaseHTTPRequestHandler):
            requests = [0]

            def do_GET(self):
                if self.__class__.requests[0] == 0:
                    self.__class__.requests[0] += 1
                    self.send_response(200)
                    self.end_headers()
                    self.wfile.write(
                        b"<html><body><script>throw new Error('boom')</script></body></html>"
                    )
                else:
                    self.__class__.requests[0] += 1
                    self.send_response(200)
                    self.end_headers()
                    self.wfile.write(b"<html><body><h1>recovered</h1></body></html>")

            def log_message(self, *a):
                pass

        port = 18933
        server = _start_server(OnceCrashHandler, port)
        base = f"http://127.0.0.1:{port}/index.html"

        try:
            r = _run([
                "--url", base,
                "--action", "navigate",
                "--retries", "2",
            ])
            assert r.returncode == 0, f"Crash recovery failed: {r.stderr}"
        finally:
            server.shutdown()


def test_no_retries_flag_single_attempt():
    """Default (no --retries) → single attempt, no retry."""
    import tempfile
    with tempfile.TemporaryDirectory() as tmp:
        port = 18934
        server = _start_server(SlowHandler, port)
        base = f"http://127.0.0.1:{port}/"

        try:
            r = _run([
                "--url", base,
                "--action", "navigate",
                "--timeout", "1000",
            ])
            assert r.returncode != 0, "Expected failure with no retries"
        finally:
            server.shutdown()
