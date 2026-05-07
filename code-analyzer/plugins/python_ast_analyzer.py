"""PythonASTAnalyzer – AST-based Python source mapping."""

import ast
from pathlib import Path
from typing import Any
from base import BaseAnalyzer


class PythonASTAnalyzer(BaseAnalyzer):
    """Deep structural parsing using Python's ast module."""

    @property
    def languages(self) -> list[str]:
        return [".py"]

    def _walk_ast(self, tree: ast.Module) -> list[tuple[str, str]]:
        """Yield (identifier, feature_type) from AST nodes."""
        items: list[tuple[str, str]] = []
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) or isinstance(node, ast.AsyncFunctionDef):
                items.append((node.name, "Logic"))
            elif isinstance(node, ast.ClassDef):
                items.append((node.name, "Component"))
                for item in node.body:
                    if isinstance(item, ast.FunctionDef) or isinstance(item, ast.AsyncFunctionDef):
                        items.append((f"{node.name}.{item.name}", "Logic"))
        return items

    @staticmethod
    def _count_complexity(tree: ast.Module) -> int:
        """Simple cyclomatic-ish score: count branches + loops."""
        score = 1
        for node in ast.walk(tree):
            if isinstance(node, (ast.If, ast.For, ast.While, ast.ExceptHandler, ast.Assert)):
                score += 1
            elif isinstance(node, ast.BoolOp):
                score += len(node.values) - 1
        return score

    def analyze(self, target: Path) -> list[dict[str, Any]]:
        results: list[dict[str, Any]] = []
        target_path = target.resolve()

        if target_path.is_file():
            files = [target_path] if target_path.suffix in self.languages else []
        else:
            files = [
                p for p in target_path.rglob("*.py") if p.is_file()
            ]

        for f in files:
            try:
                source = f.read_text(encoding="utf-8", errors="replace")
                tree = ast.parse(source, filename=str(f))
            except SyntaxError:
                continue

            items = self._walk_ast(tree)
            complexity = self._count_complexity(tree)

            results.append({
                "file_path": str(f),
                "feature_type": "Logic" if items else "Component",
                "identifiers": [name for name, _ in items],
                "complexity_score": complexity,
            })

        return results
