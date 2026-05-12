"""Tests for plugins/markdownify_backend.py."""

from plugins.markdownify_backend import MarkdownifyBackend


class TestMarkdownifyBackend:
    def setup_method(self):
        self.conv = MarkdownifyBackend()

    def test_name(self):
        assert self.conv.name == "markdownifybackend"

    def test_heading(self):
        md = self.conv.convert("<h1>Title</h1>")
        assert "# Title" in md

    def test_paragraph(self):
        md = self.conv.convert("<p>Hello world</p>")
        assert "Hello world" in md

    def test_bold(self):
        md = self.conv.convert("<strong>bold</strong>")
        assert "**bold**" in md

    def test_link(self):
        md = self.conv.convert('<a href="https://x.com">link</a>')
        assert "[link](https://x.com)" in md

    def test_unordered_list(self):
        md = self.conv.convert("<ul><li>A</li><li>B</li></ul>")
        assert "- A" in md
        assert "- B" in md

    def test_ordered_list(self):
        md = self.conv.convert("<ol><li>First</li><li>Second</li></ol>")
        assert "1. First" in md

    def test_table(self):
        html = "<table><tr><th>H</th></tr><tr><td>C</td></tr></table>"
        md = self.conv.convert(html)
        assert "H" in md
        assert "C" in md

    def test_strip_script(self):
        html = "<p>keep</p><script>alert(1)</script>"
        md = self.conv.convert(html)
        assert "alert" not in md

    def test_strip_style(self):
        html = "<p>keep</p><style>body{color:red}</style>"
        md = self.conv.convert(html)
        assert "color:red" not in md
