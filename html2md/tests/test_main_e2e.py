"""End-to-end tests for main.py CLI."""

import subprocess
import sys
import os

MAIN = sys.executable, "main.py"
CWD = "/workspace/pi-tools/html2md"


def _run(*args):
    return subprocess.run(
        (*MAIN, *args), capture_output=True, text=True, cwd=CWD
    )


class TestCLI:
    def test_no_args_exits_1(self):
        r = _run()
        assert r.returncode == 1

    def test_html_flag(self):
        r = _run("--html", "<h1>Hello</h1>")
        assert r.returncode == 0
        assert "# Hello" in r.stdout

    def test_file_flag(self):
        path = "/tmp/_test_input.html"
        with open(path, "w") as f:
            f.write("<h2>FromFile</h2>")
        try:
            r = _run("--file", path)
            assert r.returncode == 0
            assert "# FromFile" in r.stdout
        finally:
            os.unlink(path)

    def test_file_not_found(self):
        r = _run("--file", "/nonexistent.html")
        assert r.returncode == 1

    def test_backend_flag(self):
        r = _run("--html", "<h1>X</h1>", "--backend", "html2text")
        assert r.returncode == 0
        assert "X" in r.stdout

    def test_output_flag(self):
        out = "/tmp/_test_output.md"
        if os.path.exists(out):
            os.unlink(out)
        r = _run("--html", "<p>out</p>", "--output", out)
        assert r.returncode == 0
        assert os.path.exists(out)
        content = open(out).read()
        assert "out" in content
        os.unlink(out)

    def test_stdin(self):
        r = subprocess.run(
            (MAIN[0], MAIN[1]),
            input="<h1>Stdin</h1>",
            capture_output=True, text=True, cwd=CWD,
        )
        assert r.returncode == 0
        assert "# Stdin" in r.stdout

    def test_invalid_backend(self):
        r = _run("--html", "<p>x</p>", "--backend", "bad")
        assert r.returncode == 2  # argparse exit code
