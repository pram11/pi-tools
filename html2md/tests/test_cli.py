"""Tests for main.py CLI entry point."""

import subprocess
import sys

MAIN = sys.executable, "main.py"


def test_no_args_exits_1():
    """No input → error exit code."""
    result = subprocess.run(MAIN, capture_output=True, text=True)
    assert result.returncode == 1


def test_html_flag_passes_string():
    """--html flag accepts string input."""
    result = subprocess.run(
        (*MAIN, "--html", "<h1>Hello</h1>"), capture_output=True, text=True
    )
    assert result.returncode == 0


def test_file_flag_missing_file_exits_1():
    """--file with nonexistent path → error."""
    result = subprocess.run(
        (*MAIN, "--file", "/nonexistent.html"), capture_output=True, text=True
    )
    assert result.returncode == 1


def test_backend_flag_accepts_valid():
    """--backend markdownify accepted."""
    result = subprocess.run(
        (*MAIN, "--html", "<p>hi</p>", "--backend", "markdownify"),
        capture_output=True, text=True,
    )
    assert result.returncode == 0
