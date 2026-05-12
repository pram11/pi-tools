"""Resolve sibling skill paths relative to skill root."""

from pathlib import Path


class SkillPathResolver:
    """Resolves paths to sibling skills (playwright, html2md)."""

    def __init__(self, skill_root: Path):
        self.skill_root = skill_root.resolve()

    @property
    def playwright_path(self) -> Path:
        return (self.skill_root / "../playwright").resolve()

    @property
    def html2md_path(self) -> Path:
        return (self.skill_root / "../html2md").resolve()
