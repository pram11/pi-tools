"""HTML parser — sanitize and build BeautifulSoup tree."""

from bs4 import BeautifulSoup, Tag


def parse(html: str) -> BeautifulSoup:
    """Parse raw HTML → sanitized BeautifulSoup object.

    Strips <script> and <style> tags.
    """
    soup = BeautifulSoup(html, "lxml")
    for tag in soup.find_all(["script", "style", "noscript"]):
        tag.decompose()
    return soup


def get_text_html(soup: BeautifulSoup) -> str:
    """Return inner HTML string from soup (for converter ingestion)."""
    return str(soup)
