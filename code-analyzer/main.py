#!/usr/bin/env python3
"""Entry point – dynamic plugin discovery and analysis orchestration."""

import sys
from pathlib import Path
from importlib import import_module
from base import BaseAnalyzer

PLUGINS_DIR = Path(__file__).parent / "plugins"


def _discover_plugins() -> list[BaseAnalyzer]:
    """Scan plugins/ for subclasses of BaseAnalyzer."""
    plugins: list[BaseAnalyzer] = []
    if not PLUGINS_DIR.is_dir():
        return plugins

    for mod_file in PLUGINS_DIR.glob("*.py"):
        if mod_file.stem.startswith("_"):
            continue
        sys.path.insert(0, str(PLUGINS_DIR.parent))
        try:
            mod = import_module(f"plugins.{mod_file.stem}")
            for attr_name in dir(mod):
                attr = getattr(mod, attr_name)
                if (
                    isinstance(attr, type)
                    and issubclass(attr, BaseAnalyzer)
                    and attr is not BaseAnalyzer
                ):
                    plugins.append(attr())
        except ImportError:
            pass
    return plugins


def _detect_languages(target: Path) -> list[str]:
    """Heuristic: detect languages from file extensions in target."""
    exts = set()
    for p in target.rglob("*"):
        if p.is_file() and p.suffix:
            exts.add(p.suffix)
    return sorted(exts)


def analyze(target: Path, lang_filter: str | None = None) -> list[dict]:
    """Run all matching analyzers on target."""
    plugins = _discover_plugins()
    if not plugins:
        raise RuntimeError("No analyzer plugins found in plugins/")

    findings: list[dict] = []
    target_langs = set()
    if lang_filter:
        target_langs = {l.strip() for l in lang_filter.split(",")}

    for plugin in plugins:
        # If filter given, only run if plugin covers requested lang
        if target_langs and not set(plugin.languages) & target_langs:
            continue
        try:
            findings.extend(plugin.analyze(target))
        except Exception as e:
            print(f"[WARN] Plugin {plugin.__class__.__name__} failed: {e}")
    return findings


if __name__ == "__main__":
    import json
    target = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(".")
    lang = sys.argv[2] if len(sys.argv) > 2 else None
    results = analyze(target, lang)
    print(json.dumps(results, indent=2))
