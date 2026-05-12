"""Tests for main.py CLI interface."""

from pathlib import Path
import subprocess, sys

MAIN = Path(__file__).resolve().parent.parent / "main.py"
PY = sys.executable


def _run(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run([PY, str(MAIN)] + list(args), capture_output=True, text=True)


def test_no_args_shows_usage():
    result = _run()
    assert result.returncode != 0
    assert "usage" in result.stderr.lower() or "error" in result.stderr.lower()


def test_url_missing_shows_error():
    result = _run("--action", "page-to-md")
    assert result.returncode != 0
    assert "url" in result.stderr.lower() or "error" in result.stderr.lower()


def test_version_flag():
    result = _run("--version")
    assert result.returncode == 0
    assert "0.1.0" in result.stdout


def test_help_flag():
    result = _run("--help")
    assert result.returncode == 0
    assert "page-to-md" in result.stdout
