#!/usr/bin/env python3
"""Benchmark: code-analyzer vs Depwire symbol extraction."""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from plugins.python_ast_analyzer import PythonASTAnalyzer
from plugins.jsx_ast_analyzer import JSXASTAnalyzer
from plugins.regex_analyzer import RegexAnalyzer


def run_benchmark(target: Path) -> dict:
    """Run all analyzers and return benchmark results."""
    analyzers = [
        ("PythonASTAnalyzer", PythonASTAnalyzer()),
        ("JSXASTAnalyzer", JSXASTAnalyzer()),
        ("RegexAnalyzer", RegexAnalyzer()),
    ]

    results = {}
    for name, analyzer in analyzers:
        findings = analyzer.analyze(target)
        total_ids = sum(len(f.get("identifiers", [])) for f in findings)
        results[name] = {
            "files": len(findings),
            "identifiers": total_ids,
        }

    return results


def main():
    target = Path(".")
    if len(sys.argv) > 1:
        target = Path(sys.argv[1])

    results = run_benchmark(target)

    # Depwire baseline (code-analyzer repo)
    depwire_baseline = {"files": 16, "symbols": 214}

    print("=" * 50)
    print("Benchmark: code-analyzer vs Depwire")
    print("=" * 50)
    print(f"\nDepwire Baseline: {depwire_baseline['symbols']} symbols, {depwire_baseline['files']} files")
    print("-" * 50)

    for name, data in results.items():
        coverage = data["identifiers"] / depwire_baseline["symbols"] * 100
        print(f"{name}:")
        print(f"  Files: {data['files']}")
        print(f"  Identifiers: {data['identifiers']}")
        print(f"  Coverage: {coverage:.1f}%")

    # PythonASTAnalyzer is the primary comparator
    py_data = results["PythonASTAnalyzer"]
    py_coverage = py_data["identifiers"] / depwire_baseline["symbols"] * 100

    print("-" * 50)
    print(f"\nPrimary (PythonASTAnalyzer) coverage: {py_coverage:.1f}%")
    print(f"Gap: Depwire counts imports/constants/class methods")
    print(f"code-analyzer focuses on: functions, classes, methods")

    return 0 if py_coverage >= 50 else 1


if __name__ == "__main__":
    sys.exit(main())
