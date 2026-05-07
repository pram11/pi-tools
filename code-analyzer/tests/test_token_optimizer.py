"""Token optimizer tests."""

from lib.token_optimizer import condense_report


def _sample_report(findings_count: int = 10) -> dict:
    findings = [
        {
            "file_path": f"/src/mod{i}.py",
            "feature_type": "Logic",
            "identifiers": [f"func_{i}"],
            "complexity_score": i + 1,
        }
        for i in range(findings_count)
    ]
    return {
        "metadata": {
            "target": "/src",
            "languages": ["python"],
            "total_files": findings_count,
            "total_findings": findings_count,
            "generated_at": "2025-01-01T00:00:00+00:00",
        },
        "findings": findings,
        "summary": {"avg_complexity": 5.5, "max_complexity": 11, "min_complexity": 1},
    }


def test_condensed_is_shorter_json():
    report = _sample_report(20)
    full_len = len(str(report))
    condensed = condense_report(report)
    short_len = len(str(condensed))
    assert short_len < full_len, f"No savings: {short_len} vs {full_len}"


def test_condensed_groups_by_feature_type():
    report = _sample_report(5)
    condensed = condense_report(report)
    assert "grouped" in condensed
    assert "Logic" in condensed["grouped"]


def test_condensed_preserves_metadata():
    report = _sample_report()
    condensed = condense_report(report)
    meta = condensed["metadata"]
    assert meta["target"] == "/src"
    assert meta["languages"] == ["python"]


def test_condensed_merges_identifiers():
    report = _sample_report(3)
    condensed = condense_report(report)
    logic_group = condensed["grouped"]["Logic"]
    all_ids = logic_group["identifiers"]
    assert len(all_ids) == 3
    assert "func_0" in all_ids
    assert "func_1" in all_ids


def test_condensed_keeps_complexity_summary():
    report = _sample_report(4)
    condensed = condense_report(report)
    summary = condensed["summary"]
    assert summary["avg"] == report["summary"]["avg_complexity"]
    assert summary["max"] == report["summary"]["max_complexity"]


def test_condensed_uses_relative_paths():
    report = _sample_report(2)
    condensed = condense_report(report)
    logic = condensed["grouped"]["Logic"]
    paths = logic["files"]
    for p in paths:
        assert not p.startswith("/"), f"Path should be relative: {p}"


def test_empty_report_no_crash():
    empty = {"metadata": {}, "findings": [], "summary": {}}
    condensed = condense_report(empty)
    assert condensed["grouped"] == {}
    assert condensed["total_files"] == 0
