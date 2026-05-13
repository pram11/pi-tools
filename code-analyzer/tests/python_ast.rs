use std::path::PathBuf;

use code_analyzer::analyzers::PythonAnalyzer;
use code_analyzer::analyzer::Analyzer;
use tempfile::tempdir;

fn write_sample(content: &str) -> (tempfile::TempDir, PathBuf) {
    let dir = tempdir().unwrap();
    let path = dir.path().join("test.py");
    std::fs::write(&path, content).unwrap();
    (dir, path)
}

#[test]
fn test_extract_functions() {
    let (dir, target) = write_sample("def hello(): pass\ndef world(x): return x");
    let _ = dir; // keep alive
    let analyzer = PythonAnalyzer::new();
    let findings = analyzer.analyze(&target).unwrap();
    let ids: Vec<_> = findings.iter().flat_map(|f| &f.identifiers).collect();
    assert!(ids.iter().any(|i| *i == "hello"), "Missing 'hello'");
    assert!(ids.iter().any(|i| *i == "world"), "Missing 'world'");
}

#[test]
fn test_extract_classes() {
    let (dir, target) = write_sample("class Foo:\n    def bar(self): pass");
    let _ = dir;
    let analyzer = PythonAnalyzer::new();
    let findings = analyzer.analyze(&target).unwrap();
    let ids: Vec<_> = findings.iter().flat_map(|f| &f.identifiers).collect();
    assert!(ids.iter().any(|i| *i == "Foo"), "Missing 'Foo'");
    assert!(ids.iter().any(|i| i.starts_with("bar")), "Missing 'bar'");
}

#[test]
fn test_ignores_non_python_files() {
    let dir = tempdir().unwrap();
    std::fs::write(dir.path().join("readme.md"), "# hi").unwrap();
    let analyzer = PythonAnalyzer::new();
    let findings = analyzer.analyze(dir.path()).unwrap();
    assert!(findings.is_empty());
}

#[test]
fn test_complexity_score_set() {
    let dir = tempdir().unwrap();
    std::fs::write(dir.path().join("x.py"), "def f(): pass").unwrap();
    let analyzer = PythonAnalyzer::new();
    let findings = analyzer.analyze(dir.path()).unwrap();
    assert_eq!(findings.len(), 1);
    assert!(findings[0].complexity_score > 0);
}
