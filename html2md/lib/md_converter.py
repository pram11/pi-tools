"""Core conversion engine — strategy dispatcher + post-processing."""

from lib.post_processor import process
from plugins.markdownify_backend import MarkdownifyBackend
from plugins.html2text_backend import Html2textBackend

_BACKENDS = {
    "markdownify": MarkdownifyBackend,
    "html2text": Html2textBackend,
}


def get_converter(name: str = "markdownify"):
    cls = _BACKENDS.get(name)
    if cls is None:
        raise ValueError(f"Unknown backend: {name!r}. Choices: {list(_BACKENDS)}")
    return cls()


def convert(html: str, backend: str = "markdownify") -> str:
    return process(get_converter(backend).convert(html))
