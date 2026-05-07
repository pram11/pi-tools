"""E2E report wrapper tests."""

import json
import tempfile
from pathlib import Path
from lib.e2e_report import build_report
from main import analyze
from lib.project_detector import ProjectDetector


def _make_project(files: dict[str, str]) -> Path:
    root = Path(tempfile.mkdtemp())
    for rel, content in files.items():
        (root / rel).parent.mkdir(parents=True, exist_ok=True)
        (root / rel).write_text(content)
    return root


def test_report_has_metadata():
    root = _make_project({"app.py": "def f(): pass"})
    findings = analyze(root)
    report = build_report(root, findings)
    assert "metadata" in report
    meta = report["metadata"]
    assert "target" in meta
    assert "languages" in meta
    assert "total_files" in meta
    assert "total_findings" in meta


def test_report_findings_mirrors_analysis():
    root = _make_project({"a.py": "def x(): pass", "b.py": "class C: pass"})
    findings = analyze(root)
    report = build_report(root, findings)
    assert len(report["findings"]) == len(findings)


def test_report_summary_has_complexity_stats():
    root = _make_project({"app.py": "def f(): pass\nif True: pass"})
    findings = analyze(root)
    report = build_report(root, findings)
    summary = report["summary"]
    assert "avg_complexity" in summary
    assert "max_complexity" in summary
    assert "min_complexity" in summary


def test_report_json_dumps():
    root = _make_project({"app.py": "pass"})
    findings = analyze(root)
    report = build_report(root, findings)
    text = json.dumps(report, indent=2)
    assert "metadata" in text


def test_report_detects_languages():
    root = _make_project({"requirements.txt": "flask", "app.py": "pass"})
    findings = analyze(root)
    report = build_report(root, findings)
    assert "python" in report["metadata"]["languages"]
