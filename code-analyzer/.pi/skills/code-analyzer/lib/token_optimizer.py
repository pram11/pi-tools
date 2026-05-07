"""Token optimizer – condense analysis report for LLM context windows."""

from collections import defaultdict
from pathlib import Path
from typing import Any


def condense_report(report: dict[str, Any]) -> dict[str, Any]:
    """Compress full report into compact grouped format.

    Drops redundancy: merges identifiers per feature_type,
    converts absolute paths → relative, shortens metadata keys.
    """
    findings = report.get("findings", [])
    if not findings:
        return {
            "metadata": report.get("metadata", {}),
            "grouped": {},
            "summary": {},
            "total_files": 0,
        }

    target = report.get("metadata", {}).get("target", ".")
    target_path = Path(target).resolve()

    grouped = defaultdict(lambda: {"identifiers": [], "files": set()})

    for f in findings:
        ft = f["feature_type"]
        grp = grouped[ft]
        grp["identifiers"].extend(f.get("identifiers", []))
        try:
            rel = Path(f["file_path"]).relative_to(target_path)
            grp["files"].add(str(rel))
        except ValueError:
            grp["files"].add(f["file_path"])

    grouped_dict = {}
    for ft, data in grouped.items():
        grouped_dict[ft] = {
            "identifiers": sorted(set(data["identifiers"])),
            "files": sorted(data["files"]),
        }

    summary = report.get("summary", {})
    compact_summary = {}
    if summary:
        compact_summary = {
            "avg": summary.get("avg_complexity"),
            "max": summary.get("max_complexity"),
            "min": summary.get("min_complexity"),
        }

    meta = report.get("metadata", {})
    compact_meta = {
        "target": meta.get("target"),
        "languages": meta.get("languages", []),
    }

    unique_files = set()
    for data in grouped_dict.values():
        unique_files.update(data["files"])

    return {
        "metadata": compact_meta,
        "grouped": grouped_dict,
        "summary": compact_summary,
        "total_files": len(unique_files),
    }
