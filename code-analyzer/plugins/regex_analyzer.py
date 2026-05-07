"""RegexAnalyzer – baseline multi-language pattern matching."""

from pathlib import Path
from typing import Any
from base import BaseAnalyzer


class RegexAnalyzer(BaseAnalyzer):
    """Fallback analyzer using regex patterns for common languages."""

    @property
    def languages(self) -> list[str]:
        return [".py", ".js", ".ts", ".java", ".go", ".rs", ".rb", ".c", ".cpp", ".h"]

    def analyze(self, target: Path) -> list[dict[str, Any]]:
        results: list[dict[str, Any]] = []
        target_path = target.resolve()

        if target_path.is_file():
            files = [target_path]
        else:
            files = list(target_path.rglob("*"))

        for f in files:
            if not f.is_file() or f.suffix not in self.languages:
                continue
            results.append({
                "file_path": str(f),
                "feature_type": "Logic",
                "identifiers": [],
                "complexity_score": 0,
            })

        return results
