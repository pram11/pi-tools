"""Abstract analyzer interface – Strategy Pattern contract."""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any


class BaseAnalyzer(ABC):
    """All language-specific analyzers inherit this."""

    @property
    @abstractmethod
    def languages(self) -> list[str]:
        """File extensions or language names this analyzer handles."""
        ...

    @abstractmethod
    def analyze(self, target: Path) -> list[dict[str, Any]]:
        """Return standardized feature chart entries.

        Schema per item:
        {
            "file_path": str,
            "feature_type": "Route" | "Component" | "Logic",
            "identifiers": list[str],
            "complexity_score": int,
            # optional (JS/TSX analyzers):
            "loc": int,
            "nesting_depth": int,
            "routes": list[str],
            "edges": list[{"type": str, "name": str, "source": str}],
        }
        """
        ...
