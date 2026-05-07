"""Standardized JSON output tests."""

import json
import tempfile
from pathlib import Path
from main import analyze


def _make_project(files: dict[str, str]) -> Path:
    root = Path(tempfile.mkdtemp())
    for rel, content in files.items():
        (root / rel).parent.mkdir(parents=True, exist_ok=True)
        (root / rel).write_text(content)
    return root


def test_output_is_list_of_dicts():
    root = _make_project({"app.py": "def hello(): pass"})
    results = analyze(root)
    assert isinstance(results, list)
    assert len(results) >= 1
    assert isinstance(results[0], dict)


def test_schema_has_required_keys():
    required = {"file_path", "feature_type", "identifiers", "complexity_score"}
    root = _make_project({"app.py": "class App:\n    def run(self): pass"})
    results = analyze(root)
    for item in results:
        assert required.issubset(item.keys()), f"Missing keys: {required - set(item.keys())}"


def test_feature_type_is_valid():
    valid = {"Route", "Component", "Logic"}
    root = _make_project({"app.py": "def f(): pass"})
    results = analyze(root)
    for item in results:
        assert item["feature_type"] in valid, f"Invalid: {item['feature_type']}"


def test_json_serializable():
    root = _make_project({"app.py": "x = 1"})
    results = analyze(root)
    dumped = json.dumps(results)
    parsed = json.loads(dumped)
    assert len(parsed) == len(results)


def test_file_path_is_absolute():
    root = _make_project({"app.py": "pass"})
    results = analyze(root)
    for item in results:
        assert Path(item["file_path"]).is_absolute()


def test_identifiers_is_list():
    root = _make_project({"app.py": "def a(): pass\ndef b(): pass"})
    results = analyze(root)
    for item in results:
        assert isinstance(item["identifiers"], list)


def test_complexity_is_positive_int():
    root = _make_project({"app.py": "def f(): pass"})
    results = analyze(root)
    for item in results:
        assert isinstance(item["complexity_score"], int)
        assert item["complexity_score"] >= 0
