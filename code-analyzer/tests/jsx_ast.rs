use std::path::PathBuf;

use code_analyzer::analyzers::JsxAnalyzer;
use code_analyzer::analyzer::Analyzer;
use tempfile::tempdir;

fn write_sample(content: &str, suffix: &str) -> (tempfile::TempDir, PathBuf) {
    let dir = tempdir().unwrap();
    let path = dir.path().join(format!("test{suffix}"));
    std::fs::write(&path, content).unwrap();
    (dir, path)
}

#[test]
fn test_extract_component() {
    let (dir, target) = write_sample("export function Navbar() { return <nav/>; }", ".tsx");
    let _ = dir;
    let analyzer = JsxAnalyzer::new();
    let findings = analyzer.analyze(&target).unwrap();
    let ids: Vec<_> = findings.iter().flat_map(|f| &f.identifiers).collect();
    assert!(ids.iter().any(|i| *i == "Navbar"), "Missing 'Navbar'");
}

#[test]
fn test_extract_const_component() {
    let (dir, target) = write_sample("const Hero = () => <section/>;\nexport default Hero;", ".tsx");
    let _ = dir;
    let analyzer = JsxAnalyzer::new();
    let findings = analyzer.analyze(&target).unwrap();
    let ids: Vec<_> = findings.iter().flat_map(|f| &f.identifiers).collect();
    assert!(ids.iter().any(|i| *i == "Hero"), "Missing 'Hero'");
}

#[test]
fn test_extract_hook() {
    let (dir, target) = write_sample("function useCounter() { return 0; }", ".tsx");
    let _ = dir;
    let analyzer = JsxAnalyzer::new();
    let findings = analyzer.analyze(&target).unwrap();
    let ids: Vec<_> = findings.iter().flat_map(|f| &f.identifiers).collect();
    assert!(ids.iter().any(|i| *i == "useCounter"), "Missing 'useCounter'");
}

#[test]
fn test_ignores_non_jsx_files() {
    let dir = tempdir().unwrap();
    std::fs::write(dir.path().join("readme.md"), "# hi").unwrap();
    let analyzer = JsxAnalyzer::new();
    let findings = analyzer.analyze(dir.path()).unwrap();
    assert!(findings.is_empty());
}

#[test]
fn test_complexity_score_set() {
    let dir = tempdir().unwrap();
    std::fs::write(dir.path().join("x.tsx"), "const X = () => { if (true) return <div/>; }").unwrap();
    let analyzer = JsxAnalyzer::new();
    let findings = analyzer.analyze(dir.path()).unwrap();
    assert_eq!(findings.len(), 1);
    assert!(findings[0].complexity_score > 0);
}

#[test]
fn test_loc_set() {
    let (dir, target) = write_sample("const X = () => <div/>;", ".tsx");
    let _ = dir;
    let analyzer = JsxAnalyzer::new();
    let findings = analyzer.analyze(&target).unwrap();
    assert_eq!(findings[0].loc, Some(1));
}

#[test]
fn test_nesting_depth_set() {
    let dir = tempdir().unwrap();
    let src = "const X = () => {\n  return (\n    <div>\n      <span>{a}</span>\n    </div>\n  );\n}";
    std::fs::write(dir.path().join("x.tsx"), src).unwrap();
    let analyzer = JsxAnalyzer::new();
    let findings = analyzer.analyze(dir.path()).unwrap();
    assert!(findings[0].nesting_depth.unwrap() > 0);
}

#[test]
fn test_imports_extracted() {
    let dir = tempdir().unwrap();
    let src = r#"import { useState } from "react";
import Link from "next/link";"#;
    std::fs::write(dir.path().join("x.tsx"), src).unwrap();
    let analyzer = JsxAnalyzer::new();
    let findings = analyzer.analyze(dir.path()).unwrap();
    assert_eq!(findings.len(), 1);
    let edges = findings[0].edges.as_ref().unwrap();
    assert!(edges.iter().any(|e| e.source == "react"), "Missing react import");
    assert!(edges.iter().any(|e| e.source == "next/link"), "Missing next/link import");
}

#[test]
fn test_route_discovery() {
    let dir = tempdir().unwrap();
    std::fs::create_dir_all(dir.path().join("app/blog")).unwrap();
    std::fs::write(dir.path().join("app/blog/page.tsx"), "export default () => <div/>").unwrap();
    let analyzer = JsxAnalyzer::new();
    let findings = analyzer.analyze(dir.path()).unwrap();
    let routes: Vec<_> = findings.iter().filter_map(|f| f.routes.as_ref()).collect();
    assert!(!routes.is_empty(), "Should find route");
    assert!(routes[0].iter().any(|r| r.contains("blog")), "Missing /blog route");
}

#[test]
fn test_feature_type_component() {
    let dir = tempdir().unwrap();
    std::fs::write(dir.path().join("Button.tsx"), "export function Button() { return <button/>; }").unwrap();
    let analyzer = JsxAnalyzer::new();
    let findings = analyzer.analyze(dir.path()).unwrap();
    assert_eq!(findings[0].feature_type.to_string(), "Component");
}

#[test]
fn test_feature_type_route() {
    let dir = tempdir().unwrap();
    std::fs::create_dir_all(dir.path().join("app")).unwrap();
    std::fs::write(dir.path().join("app/page.tsx"), "export default () => <div/>").unwrap();
    let analyzer = JsxAnalyzer::new();
    let findings = analyzer.analyze(dir.path()).unwrap();
    assert_eq!(findings[0].feature_type.to_string(), "Route");
}
