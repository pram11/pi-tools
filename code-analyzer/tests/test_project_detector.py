"""ProjectDetector tests."""

import tempfile
from pathlib import Path
from lib.project_detector import ProjectDetector


def _make_project(files: dict[str, str]) -> Path:
    root = Path(tempfile.mkdtemp())
    for rel, content in files.items():
        (root / rel).write_text(content)
    return root


def test_detects_python_project():
    root = _make_project({"requirements.txt": "flask", "app.py": ""})
    info = ProjectDetector.detect(root)
    assert "python" in info


def test_detects_node_project():
    root = _make_project({"package.json": "{}", "index.js": ""})
    info = ProjectDetector.detect(root)
    assert "javascript" in info or "node" in info


def test_detects_java_project():
    root = _make_project({"pom.xml": "<project/>", "App.java": ""})
    info = ProjectDetector.detect(root)
    assert "java" in info


def test_detects_mixed_project():
    root = _make_project({
        "requirements.txt": "",
        "package.json": "{}",
    })
    info = ProjectDetector.detect(root)
    assert len(info) >= 2


def test_empty_dir_returns_unknown():
    root = Path(tempfile.mkdtemp())
    info = ProjectDetector.detect(root)
    assert "unknown" in info
