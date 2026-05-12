"""Primary converter backend — markdownify."""

from markdownify import markdownify as md

from base import BaseConverter
from lib.html_parser import parse, get_text_html


class MarkdownifyBackend(BaseConverter):
    def convert(self, html: str) -> str:
        soup = parse(html)
        clean = get_text_html(soup)
        return md(clean, heading_style="atx", bullets="-")
