"""Plugin discovery tests."""

from pathlib import Path
from main import _discover_plugins
from base import BaseAnalyzer


def test_discovers_at_least_one_plugin():
    plugins = _discover_plugins()
    assert len(plugins) >= 1, "Expected at least one registered plugin"


def test_discovered_plugins_are_analyzers():
    plugins = _discover_plugins()
    for p in plugins:
        assert isinstance(p, BaseAnalyzer)


def test_plugins_declare_languages():
    plugins = _discover_plugins()
    for p in plugins:
        assert len(p.languages) > 0, f"{p.__class__.__name__} declares no languages"


def test_plugins_have_analyze_method():
    plugins = _discover_plugins()
    for p in plugins:
        assert callable(getattr(p, "analyze", None))
