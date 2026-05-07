"""PythonASTAnalyzer tests."""

import tempfile
from pathlib import Path
from plugins.python_ast_analyzer import PythonASTAnalyzer


def _write_sample(content: str) -> Path:
    p = Path(tempfile.mktemp(suffix=".py"))
    p.write_text(content)
    return p


def test_extract_functions():
    src = "def hello(): pass\ndef world(x): return x"
    target = _write_sample(src)
    analyzer = PythonASTAnalyzer()
    findings = analyzer.analyze(target)
    ids = [f["identifiers"] for f in findings]
    assert any("hello" in i for i in ids), "Missing 'hello'"
    assert any("world" in i for i in ids), "Missing 'world'"


def test_extract_classes():
    src = "class Foo:\n    def bar(self): pass"
    target = _write_sample(src)
    analyzer = PythonASTAnalyzer()
    findings = analyzer.analyze(target)
    ids = [f["identifiers"] for f in findings]
    assert any("Foo" in i for i in ids), "Missing 'Foo'"
    assert any("bar" in i for i in ids), "Missing 'bar'"


def test_ignores_non_python_files(tmp_path: Path):
    (tmp_path / "readme.md").write_text("# hi")
    analyzer = PythonASTAnalyzer()
    findings = analyzer.analyze(tmp_path)
    assert len(findings) == 0


def test_complexity_score_set(tmp_path: Path):
    (tmp_path / "x.py").write_text("def f(): pass")
    analyzer = PythonASTAnalyzer()
    findings = analyzer.analyze(tmp_path)
    assert len(findings) == 1
    assert findings[0]["complexity_score"] > 0
