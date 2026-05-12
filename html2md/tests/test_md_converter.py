"""Tests for lib/md_converter.py — strategy dispatcher."""

from lib.md_converter import get_converter, convert


class TestGetConverter:
    def test_returns_markdownify_default(self):
        c = get_converter()
        assert c.name == "markdownifybackend"

    def test_returns_markdownify_explicit(self):
        c = get_converter("markdownify")
        assert c.name == "markdownifybackend"

    def test_returns_html2text(self):
        c = get_converter("html2text")
        assert c.name == "html2textbackend"

    def test_invalid_backend_raises(self):
        import pytest
        with pytest.raises(ValueError):
            get_converter("invalid")


class TestConvert:
    def test_convert_default(self):
        md = convert("<h1>Hi</h1>")
        assert "# Hi" in md

    def test_convert_html2text(self):
        md = convert("<h1>Hi</h1>", backend="html2text")
        assert "Hi" in md
