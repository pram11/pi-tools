"""Auth flows — cookie injection, localStorage seeding, token auth."""

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


def _start_server(tmpdir: str, port: int = 18930) -> tuple:
    __import__("os").chdir(tmpdir)
    server = HTTPServer(("127.0.0.1", port), SimpleHTTPRequestHandler)
    t = threading.Thread(target=server.serve_forever, daemon=True)
    t.start()
    return server, t


def test_inject_cookies_session():
    """Inject cookies via session, verify in subsequent invocation."""
    with tempfile.TemporaryDirectory() as tmp:
        html = Path(tmp) / "index.html"
        html.write_text('<h1>cookie-test</h1>')

        port = 18930
        server, _ = _start_server(tmp, port)
        base = f"http://127.0.0.1:{port}/index.html"

        try:
            # 1. session-start
            r = _run(["session-start", "--url", base])
            assert r.returncode == 0, f"session-start failed: {r.stderr}"

            # 2. inject cookies (uses session context)
            cookies = json.dumps([
                {"name": "auth_token", "value": "abc123", "domain": "127.0.0.1", "path": "/"}
            ])
            r = _run([
                "--url", base,
                "--action", "auth-inject",
                "--value", cookies,
                "--output", "cookies",
            ])
            assert r.returncode == 0, f"auth-inject cookies failed: {r.stderr}"

            # 3. verify cookie in SAME session (new invocation)
            r = _run([
                "--action", "eval",
                "--value", "document.cookie",
            ])
            assert r.returncode == 0, f"eval failed: {r.stderr}"
            assert "auth_token=abc123" in r.stdout, f"Cookie not present. Got: {r.stdout}"

            # 4. session-stop
            r = _run(["session-stop"])
            assert r.returncode == 0
        finally:
            server.shutdown()


def test_seed_localstorage_session():
    """Seed localStorage via session, verify in subsequent invocation."""
    with tempfile.TemporaryDirectory() as tmp:
        html = Path(tmp) / "index.html"
        html.write_text('<h1>ls-test</h1>')

        port = 18931
        server, _ = _start_server(tmp, port)
        base = f"http://127.0.0.1:{port}/index.html"

        try:
            # 1. session-start
            r = _run(["session-start", "--url", base])
            assert r.returncode == 0, f"session-start failed: {r.stderr}"

            # 2. seed localStorage
            ls_data = json.dumps({"user_id": "42", "theme": "dark"})
            r = _run([
                "--url", base,
                "--action", "auth-inject",
                "--value", ls_data,
                "--output", "localStorage",
            ])
            assert r.returncode == 0, f"auth-inject localStorage failed: {r.stderr}"

            # 3. verify in new invocation (uses session storage_state)
            r = _run([
                "--action", "eval",
                "--value", "localStorage.getItem('user_id')",
            ])
            assert r.returncode == 0, f"eval failed: {r.stderr}"
            assert "42" in r.stdout, f"user_id not seeded. Got: {r.stdout}"

            r = _run([
                "--action", "eval",
                "--value", "localStorage.getItem('theme')",
            ])
            assert r.returncode == 0
            assert "dark" in r.stdout

            # 4. session-stop
            r = _run(["session-stop"])
            assert r.returncode == 0
        finally:
            server.shutdown()


def test_auth_flow_combined_session():
    """Combined auth: cookies + localStorage via session."""
    with tempfile.TemporaryDirectory() as tmp:
        html = Path(tmp) / "index.html"
        html.write_text('<h1>combined-auth</h1>')

        port = 18932
        server, _ = _start_server(tmp, port)
        base = f"http://127.0.0.1:{port}/index.html"

        try:
            # 1. session-start
            r = _run(["session-start", "--url", base])
            assert r.returncode == 0

            # 2. combined auth data
            auth_data = json.dumps({
                "cookies": [
                    {"name": "session_id", "value": "sess-999", "domain": "127.0.0.1", "path": "/"}
                ],
                "localStorage": {
                    "auth_state": "logged_in",
                    "user": "admin"
                }
            })
            r = _run([
                "--url", base,
                "--action", "auth-inject",
                "--value", auth_data,
            ])
            assert r.returncode == 0, f"combined auth-inject failed: {r.stderr}"

            # 3. verify cookie
            r = _run(["--action", "eval", "--value", "document.cookie"])
            assert r.returncode == 0
            assert "session_id=sess-999" in r.stdout

            # 4. verify localStorage
            r = _run(["--action", "eval", "--value", "localStorage.getItem('auth_state')"])
            assert r.returncode == 0
            assert "logged_in" in r.stdout

            # 5. session-stop
            r = _run(["session-stop"])
            assert r.returncode == 0
        finally:
            server.shutdown()


def test_auth_clear_session():
    """Clear auth state (cookies + localStorage) in session."""
    with tempfile.TemporaryDirectory() as tmp:
        html = Path(tmp) / "index.html"
        html.write_text('<h1>clear-test</h1>')

        port = 18933
        server, _ = _start_server(tmp, port)
        base = f"http://127.0.0.1:{port}/index.html"

        try:
            # 1. session-start
            r = _run(["session-start", "--url", base])
            assert r.returncode == 0

            # 2. inject auth
            cookies = json.dumps([
                {"name": "tok", "value": "v", "domain": "127.0.0.1", "path": "/"}
            ])
            r = _run([
                "--url", base,
                "--action", "auth-inject",
                "--value", cookies,
                "--output", "cookies",
            ])
            assert r.returncode == 0

            # 3. set localStorage
            r = _run([
                "--action", "eval",
                "--value", "localStorage.setItem('secret', 'val');",
            ])
            assert r.returncode == 0

            # 4. clear auth
            r = _run(["--action", "auth-clear"])
            assert r.returncode == 0, f"auth-clear failed: {r.stderr}"

            # 5. verify cleared
            r = _run(["--action", "eval", "--value", "document.cookie"])
            assert r.returncode == 0
            assert "tok" not in r.stdout

            r = _run(["--action", "eval", "--value", "localStorage.getItem('secret')"])
            assert r.returncode == 0
            assert "val" not in r.stdout

            # 6. session-stop
            r = _run(["session-stop"])
            assert r.returncode == 0
        finally:
            server.shutdown()


def test_seed_headers_unit():
    """Unit test: seed_headers sets extra HTTP headers on context."""
    import main
    from unittest.mock import MagicMock

    ctx = MagicMock()
    main.seed_headers(ctx, {"X-Auth-Token": "secret", "X-Custom": "val"})
    ctx.set_extra_http_headers.assert_called_once_with(
        {"X-Auth-Token": "secret", "X-Custom": "val"}
    )


def test_inject_cookies_unit():
    """Unit test: inject_cookies calls context.add_cookies with correct params."""
    import main
    from unittest.mock import MagicMock

    ctx = MagicMock()
    cookies = [
        {"name": "token", "value": "abc", "domain": "example.com", "path": "/"},
    ]
    main.inject_cookies(ctx, cookies, "https://example.com/page")
    ctx.add_cookies.assert_called()
    call_args = ctx.add_cookies.call_args[0][0]
    assert call_args[0]["name"] == "token"
    assert call_args[0]["value"] == "abc"
    assert call_args[0]["domain"] == "example.com"
    assert call_args[0]["path"] == "/"
