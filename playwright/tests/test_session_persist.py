"""Persistent browser context — cookies & localStorage survive across invocations."""

import json
import subprocess
import sys
import tempfile
import threading
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path

MAIN = Path(__file__).parent.parent / "main.py"
PYTHON = sys.executable


def _run(args: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(
        [PYTHON, str(MAIN)] + args,
        capture_output=True, text=True, timeout=30,
    )


def _start_server(tmpdir: str, port: int = 18923) -> tuple[HTTPServer, threading.Thread]:
    os_chdir = __import__("os")
    os_chdir.chdir(tmpdir)
    server = HTTPServer(("127.0.0.1", port), SimpleHTTPRequestHandler)
    t = threading.Thread(target=server.serve_forever, daemon=True)
    t.start()
    return server, t


def test_session_cookies_persist_across_invocations():
    """cookie set in one invocation → read in a new invocation (same session)."""
    import tempfile, os
    with tempfile.TemporaryDirectory() as tmp:
        # serve a real page so cookies work
        html = Path(tmp) / "index.html"
        html.write_text("<h1>session-test</h1>")

        port = 18924
        server, _ = _start_server(tmp, port)
        base = f"http://127.0.0.1:{port}/index.html"

        try:
            # 1. session-start
            r = _run(["session-start", "--url", base])
            assert r.returncode == 0, f"session-start failed: {r.stderr}"

            # 2. set cookie
            r = _run(["--action", "eval",
                       "--value", "document.cookie='test_key=hello';"])
            assert r.returncode == 0, f"set cookie failed: {r.stderr}"

            # 3. read cookie in NEW invocation (no --url → uses session)
            r = _run(["--action", "eval",
                       "--value", "document.cookie"])
            assert r.returncode == 0, f"read cookie failed: {r.stderr}"
            assert "test_key=hello" in r.stdout, \
                f"Cookie not persisted. Got: {r.stdout}"

            # 4. session-stop
            r = _run(["session-stop"])
            assert r.returncode == 0, f"session-stop failed: {r.stderr}"
        finally:
            server.shutdown()


def test_session_localstorage_persist_across_invocations():
    """localStorage survives across separate CLI invocations."""
    import tempfile
    with tempfile.TemporaryDirectory() as tmp:
        html = Path(tmp) / "index.html"
        html.write_text("<h1>session-test</h1>")

        port = 18925
        server, _ = _start_server(tmp, port)
        base = f"http://127.0.0.1:{port}/index.html"

        try:
            # 1. session-start
            r = _run(["session-start", "--url", base])
            assert r.returncode == 0, f"session-start failed: {r.stderr}"

            # 2. set localStorage
            r = _run(["--action", "eval",
                       "--value", "localStorage.setItem('persist_key','persist_val');"])
            assert r.returncode == 0, f"set LS failed: {r.stderr}"

            # 3. read localStorage in NEW invocation
            r = _run(["--action", "eval",
                       "--value", "localStorage.getItem('persist_key')"])
            assert r.returncode == 0, f"read LS failed: {r.stderr}"
            assert "persist_val" in r.stdout, \
                f"localStorage not persisted. Got: {r.stdout}"

            # 4. session-stop
            r = _run(["session-stop"])
            assert r.returncode == 0
        finally:
            server.shutdown()
