"""Shared file filtering utilities."""

from pathlib import Path

_DEFAULT_EXCLUDE_DIRS = {
    ".venv", "__pycache__", ".git", "node_modules",
    ".pytest_cache", ".mypy_cache", ".tox", "venv", "env",
    "dist", "build", ".eggs", "*.egg-info",
}


def _should_exclude(path: Path, exclude_dirs: set[str] | None = None) -> bool:
    """Check if any parent directory matches exclusion list."""
    dirs = exclude_dirs or _DEFAULT_EXCLUDE_DIRS
    parts = path.parts
    for part in parts:
        if part in dirs:
            return True
        # Handle wildcard patterns
        for pattern in dirs:
            if pattern.startswith("*") and part.endswith(pattern[1:]):
                return True
    return False


def iter_sources(root: Path, extensions: list[str], exclude_dirs: set[str] | None = None) -> list[Path]:
    """Walk root, yield files matching extensions, skipping excluded dirs."""
    results = []
    for p in root.rglob("*"):
        if not p.is_file():
            continue
        if p.suffix not in extensions:
            continue
        if _should_exclude(p, exclude_dirs):
            continue
        results.append(p)
    return results
