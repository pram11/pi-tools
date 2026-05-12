"""Tests for lib/post_processor.py."""

from lib.post_processor import process


class TestPostProcessor:
    def test_dedup_blank_lines(self):
        md = "A\n\n\n\nB"
        assert process(md) == "A\n\nB"

    def test_strip_trailing_spaces(self):
        md = "Hello   \nWorld  "
        assert process(md) == "Hello\nWorld"

    def test_remove_leading_blank_lines(self):
        md = "\n\n\n# Title"
        assert process(md).startswith("#")

    def test_remove_trailing_blank_lines(self):
        md = "# Title\n\n\n"
        assert process(md).endswith("# Title")

    def test_identity_on_clean_input(self):
        md = "# Title\n\nParagraph"
        assert process(md) == md
