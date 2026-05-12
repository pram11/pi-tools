"""Fallback converter backend — html2text."""

import html2text

from base import BaseConverter
from lib.html_parser import parse, get_text_html


class Html2textBackend(BaseConverter):
    def convert(self, html: str) -> str:
        soup = parse(html)
        clean = get_text_html(soup)
        h = html2text.HTML2Text()
        h.body_width = 0  # no auto-wrap
        h.skip_internal_links = False
        h.inline_links = True
        h.protect_links = True
        h.single_line_break = True
        return h.handle(clean).strip()
