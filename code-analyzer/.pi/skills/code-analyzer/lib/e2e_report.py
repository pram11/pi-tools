"""E2E report builder – standardized JSON wrapper for downstream consumers."""

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from lib.project_detector import ProjectDetector


def build_report(target: Path, findings: list[dict[str, Any]]) -> dict[str, Any]:
    """Wrap raw findings in a structured E2E report.

    Schema:
    {
        "metadata": { target, languages, total_files, total_findings, generated_at },
        "findings": [ ... ],
        "summary": { avg_complexity, max_complexity, min_complexity },
    }
    """
    languages = ProjectDetector.detect(target)
    complexities = [f["complexity_score"] for f in findings if "complexity_score" in f]

    summary: dict[str, Any] = {}
    if complexities:
        summary = {
            "avg_complexity": round(sum(complexities) / len(complexities), 2),
            "max_complexity": max(complexities),
            "min_complexity": min(complexities),
        }

    unique_files = {f["file_path"] for f in findings}

    return {
        "metadata": {
            "target": str(target.resolve()),
            "languages": languages,
            "total_files": len(unique_files),
            "total_findings": len(findings),
            "generated_at": datetime.now(timezone.utc).isoformat(),
        },
        "findings": findings,
        "summary": summary,
    }
