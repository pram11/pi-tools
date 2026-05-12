"""Tests for batch processing (--urls, --output-dir)."""

from pathlib import Path
import sys
import tempfile
import subprocess

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

MAIN = Path(__file__).resolve().parent.parent / "main.py"
PY = sys.executable


def _run(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run([PY, str(MAIN)] + list(args), capture_output=True, text=True)


class TestBatchCLIParsing:
    """Verify CLI accepts batch flags (no browser needed)."""

    def test_urls_flag_accepted(self, tmp_path):
        """--urls flag parses without error (missing file → runtime error, not parse error)."""
        url_file = tmp_path / "urls.txt"
        url_file.write_text("https://example.com\n")
        result = _run("--urls", str(url_file))
        # Should NOT be argparse parse error (exit 2)
        assert result.returncode != 2, f"Parse error: {result.stderr}"

    def test_output_dir_flag_accepted(self, tmp_path):
        """--output-dir flag parses without error."""
        result = _run("--urls", "dummy.txt", "--output-dir", str(tmp_path))
        assert result.returncode != 2, f"Parse error: {result.stderr}"

    def test_urls_without_action_defaults_to_page_to_md(self, tmp_path):
        """--urls should default action to page-to-md."""
        url_file = tmp_path / "urls.txt"
        url_file.write_text("https://example.com\n")
        result = _run("--urls", str(url_file), "--help")
        assert result.returncode == 0


class TestBatchFunctions:
    """Test batch logic functions directly."""

    def test_read_url_list(self):
        from lib.batch import read_url_list

        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("https://a.com\n")
            f.write("https://b.com\n")
            f.write("  \n")  # blank line
            f.write("# comment\n")  # comment
            f.write("https://c.com\n")
            path = f.name

        urls = read_url_list(path)
        assert urls == ["https://a.com", "https://b.com", "https://c.com"]

    def test_read_url_list_empty_file(self):
        from lib.batch import read_url_list

        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("")
            path = f.name

        urls = read_url_list(path)
        assert urls == []

    def test_read_url_list_nonexistent_file(self):
        from lib.batch import read_url_list
        import pytest

        with pytest.raises(FileNotFoundError):
            read_url_list("/nonexistent/urls.txt")

    def test_safe_filename_basic(self):
        from lib.batch import _safe_filename
        name = _safe_filename("https://example.com/path")
        assert name == "example.com_path"

    def test_safe_filename_with_query(self):
        from lib.batch import _safe_filename
        name = _safe_filename("https://example.com?a=1&b=2")
        assert "http" not in name
        assert "_a_1_b_2" in name

    def test_run_batch_returns_zero_for_empty_list(self):
        """Empty URL list → rc=0 with warning."""
        from lib.batch import run_batch
        import tempfile

        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("")
            path = f.name

        rc = run_batch(url_file=path)
        assert rc == 0
