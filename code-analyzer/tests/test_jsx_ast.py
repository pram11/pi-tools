"""JSXASTAnalyzer tests."""

import tempfile
from pathlib import Path
from plugins.jsx_ast_analyzer import JSXASTAnalyzer


def _write_sample(content: str, suffix: str = ".tsx") -> Path:
    p = Path(tempfile.mktemp(suffix=suffix))
    p.write_text(content)
    return p


def test_extract_component():
    src = "export function Navbar() { return <nav/>; }"
    target = _write_sample(src)
    analyzer = JSXASTAnalyzer()
    findings = analyzer.analyze(target)
    ids = [f["identifiers"] for f in findings]
    assert any("Navbar" in i for i in ids), "Missing 'Navbar'"


def test_extract_const_component():
    src = "const Hero = () => <section/>;\nexport default Hero;"
    target = _write_sample(src)
    analyzer = JSXASTAnalyzer()
    findings = analyzer.analyze(target)
    ids = [f["identifiers"] for f in findings]
    assert any("Hero" in i for i in ids), "Missing 'Hero'"


def test_extract_hook():
    src = "function useCounter() { return 0; }"
    target = _write_sample(src)
    analyzer = JSXASTAnalyzer()
    findings = analyzer.analyze(target)
    ids = [f["identifiers"] for f in findings]
    assert any("useCounter" in i for i in ids), "Missing 'useCounter'"


def test_ignores_non_jsx_files(tmp_path: Path):
    (tmp_path / "readme.md").write_text("# hi")
    analyzer = JSXASTAnalyzer()
    findings = analyzer.analyze(tmp_path)
    assert len(findings) == 0


def test_complexity_score_set(tmp_path: Path):
    (tmp_path / "x.tsx").write_text("const X = () => { if (true) return <div/>; }")
    analyzer = JSXASTAnalyzer()
    findings = analyzer.analyze(tmp_path)
    assert len(findings) == 1
    assert findings[0]["complexity_score"] > 0


def test_loc_set(tmp_path: Path):
    (tmp_path / "x.tsx").write_text("const X = () => <div/>;")
    analyzer = JSXASTAnalyzer()
    findings = analyzer.analyze(tmp_path)
    assert findings[0]["loc"] == 1


def test_nesting_depth_set(tmp_path: Path):
    src = "const X = () => {\n  return (\n    <div>\n      <span>{a}</span>\n    </div>\n  );\n}"
    (tmp_path / "x.tsx").write_text(src)
    analyzer = JSXASTAnalyzer()
    findings = analyzer.analyze(tmp_path)
    assert findings[0]["nesting_depth"] > 0


def test_imports_extracted(tmp_path: Path):
    src = 'import { useState } from "react";\nimport Link from "next/link";'
    (tmp_path / "x.tsx").write_text(src)
    analyzer = JSXASTAnalyzer()
    findings = analyzer.analyze(tmp_path)
    assert len(findings) == 1
    edges = findings[0].get("edges", [])
    assert any(e["source"] == "react" for e in edges), "Missing react import"
    assert any(e["source"] == "next/link" for e in edges), "Missing next/link import"


def test_route_discovery(tmp_path: Path):
    (tmp_path / "app" / "blog").mkdir(parents=True)
    (tmp_path / "app" / "blog" / "page.tsx").write_text("export default () => <div/>")
    analyzer = JSXASTAnalyzer()
    findings = analyzer.analyze(tmp_path)
    routes = [f.get("routes", []) for f in findings]
    assert any("blog" in r[0] for r in routes if r), "Missing /blog route"


def test_feature_type_component(tmp_path: Path):
    src = "export function Button() { return <button/>; }"
    (tmp_path / "Button.tsx").write_text(src)
    analyzer = JSXASTAnalyzer()
    findings = analyzer.analyze(tmp_path)
    assert findings[0]["feature_type"] == "Component"


def test_feature_type_route(tmp_path: Path):
    (tmp_path / "app").mkdir(parents=True)
    (tmp_path / "app" / "page.tsx").write_text("export default () => <div/>")
    analyzer = JSXASTAnalyzer()
    findings = analyzer.analyze(tmp_path)
    assert findings[0]["feature_type"] == "Route"
