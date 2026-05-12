"""Tests for lib.path_resolver."""

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from lib.path_resolver import SkillPathResolver


def test_skill_root_resolves():
    resolver = SkillPathResolver(Path(__file__).resolve().parent.parent)
    assert resolver.skill_root.is_absolute()
    assert resolver.skill_root.name == "playwright-md"


def test_sibling_paths_resolve():
    resolver = SkillPathResolver(Path(__file__).resolve().parent.parent)
    assert resolver.playwright_path.is_absolute()
    assert resolver.html2md_path.is_absolute()


def test_sibling_paths_point_correctly():
    resolver = SkillPathResolver(Path(__file__).resolve().parent.parent)
    assert resolver.playwright_path.name == "playwright"
    assert resolver.html2md_path.name == "html2md"
