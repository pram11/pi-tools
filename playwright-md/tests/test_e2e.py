"""End-to-end pipeline tests (no browser — mock the HTML source)."""

from pathlib import Path
import sys
import tempfile

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


class TestPipelineNoBrowser:
    """Test sanitize → convert → post-process pipeline with known inputs."""

    def test_full_pipeline_simple_html(self):
        from lib.orchestrator import sanitize_html, html_to_markdown, post_process_markdown

        raw = "<html><head><script>alert(1)</script></head><body><h1>Hello</h1><p>World</p></body></html>"
        html = sanitize_html(raw)
        md = html_to_markdown(html, backend="markdownify")
        md = post_process_markdown(md)
        assert "# Hello" in md
        assert "World" in md
        assert "<script>" not in md

    def test_full_pipeline_with_sub_region(self):
        from lib.orchestrator import extract_sub_region, sanitize_html, html_to_markdown, post_process_markdown

        raw = "<html><body><main id='content'><h2>Title</h2><p>Body</p></main><aside>Sidebar</aside></body></html>"
        html = extract_sub_region(raw, "#content")
        html = sanitize_html(html)
        md = html_to_markdown(html)
        md = post_process_markdown(md)
        assert "Title" in md
        assert "Body" in md
        assert "Sidebar" not in md

    def test_full_pipeline_html2text_backend(self):
        from lib.orchestrator import sanitize_html, html_to_markdown, post_process_markdown

        raw = "<h1>Head</h1><p>Para</p>"
        html = sanitize_html(raw)
        md = html_to_markdown(html, backend="html2text")
        md = post_process_markdown(md)
        assert "Head" in md
        assert "Para" in md

    def test_full_pipeline_preserves_tables(self):
        from lib.orchestrator import sanitize_html, html_to_markdown, post_process_markdown

        raw = "<table><tr><th>Name</th></tr><tr><td>Test</td></tr></table>"
        html = sanitize_html(raw)
        md = html_to_markdown(html)
        md = post_process_markdown(md)
        assert "Name" in md
        assert "Test" in md


class TestBatchCLIFull:
    """Test batch CLI with real file (no browser — just parse + read)."""

    def test_batch_reads_urls_and_iterates(self, tmp_path):
        from lib.batch import read_url_list
        url_file = tmp_path / "urls.txt"
        url_file.write_text("https://a.com\nhttps://b.com\nhttps://c.com\n")
        urls = read_url_list(str(url_file))
        assert len(urls) == 3

    def test_batch_handles_comments_and_blanks(self, tmp_path):
        from lib.batch import read_url_list
        url_file = tmp_path / "urls.txt"
        url_file.write_text("# Header\n\nhttps://a.com\n\n  # comment\nhttps://b.com\n")
        urls = read_url_list(str(url_file))
        assert urls == ["https://a.com", "https://b.com"]


class TestOutputToDir:
    """Test --output-dir creates files correctly (no browser)."""

    def test_output_dir_created(self, tmp_path):
        out_dir = tmp_path / "out" / "nested"
        from lib.batch import _safe_filename
        name = _safe_filename("https://example.com/page")
        file_path = out_dir / f"{name}.md"
        out_dir.mkdir(parents=True, exist_ok=True)
        file_path.write_text("# test")
        assert file_path.exists()
        assert file_path.read_text() == "# test"
