"""Base converter — abstract strategy interface."""

from abc import ABC, abstractmethod


class BaseConverter(ABC):
    """All converter backends inherit this."""

    @property
    def name(self) -> str:
        return self.__class__.__name__.lower()

    @abstractmethod
    def convert(self, html: str) -> str:
        """Convert raw HTML string → Markdown string."""
        ...
