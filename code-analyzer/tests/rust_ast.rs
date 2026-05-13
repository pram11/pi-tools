use std::fs;
use std::path::PathBuf;
use code_analyzer::analyzers::RustAnalyzer;
use code_analyzer::analyzer::Analyzer;
use tempfile::tempdir;

fn write_sample(content: &str) -> (tempfile::TempDir, PathBuf) {
    let dir = tempdir().unwrap();
    let path = dir.path().join("main.rs");
    fs::write(&path, content).unwrap();
    (dir, path)
}

#[test]
fn test_extract_functions() {
    let (dir, target) = write_sample("fn hello() {}\nfn add(a: i32, b: i32) -> i32 { a + b }");
    let _ = dir;
    let analyzer = RustAnalyzer::new();
    let findings = analyzer.analyze(&target).unwrap();
    assert!(!findings.is_empty());
    let ids: Vec<_> = findings.iter().flat_map(|f| &f.identifiers).collect();
    assert!(ids.iter().any(|i| i == &"hello"));
    assert!(ids.iter().any(|i| i == &"add"));
}

#[test]
fn test_extract_structs() {
    let (dir, target) = write_sample("struct User { name: String, age: u32 }");
    let _ = dir;
    let analyzer = RustAnalyzer::new();
    let findings = analyzer.analyze(&target).unwrap();
    assert!(!findings.is_empty());
    assert!(findings[0].identifiers.iter().any(|i| i == &"User"));
}

#[test]
fn test_extract_enums() {
    let (dir, target) = write_sample("enum Color { Red, Green, Blue }");
    let _ = dir;
    let analyzer = RustAnalyzer::new();
    let findings = analyzer.analyze(&target).unwrap();
    assert!(!findings.is_empty());
    let ids: Vec<_> = findings.iter().flat_map(|f| &f.identifiers).collect();
    assert!(ids.iter().any(|i| i == &"Color"));
    assert!(ids.iter().any(|i| i == &"Color.Red"));
    assert!(ids.iter().any(|i| i == &"Color.Green"));
    assert!(ids.iter().any(|i| i == &"Color.Blue"));
}

#[test]
fn test_extract_impl_methods() {
    let (dir, target) = write_sample(
        "struct Foo { x: i32 }\nimpl Foo { fn bar(&self) -> i32 { self.x } fn baz(&self, y: i32) { } }"
    );
    let _ = dir;
    let analyzer = RustAnalyzer::new();
    let findings = analyzer.analyze(&target).unwrap();
    assert!(!findings.is_empty());
    let ids: Vec<_> = findings.iter().flat_map(|f| &f.identifiers).collect();
    assert!(ids.iter().any(|i| i == &"Foo"));
    assert!(ids.iter().any(|i| i == &"Foo.bar"));
    assert!(ids.iter().any(|i| i == &"Foo.baz"));
}

#[test]
fn test_extract_traits() {
    let (dir, target) = write_sample("trait Drawable { fn draw(&self); }");
    let _ = dir;
    let analyzer = RustAnalyzer::new();
    let findings = analyzer.analyze(&target).unwrap();
    assert!(!findings.is_empty());
    let ids: Vec<_> = findings.iter().flat_map(|f| &f.identifiers).collect();
    assert!(ids.iter().any(|i| i == &"Drawable"));
    assert!(ids.iter().any(|i| i == &"Drawable.draw"));
}

#[test]
fn test_extract_imports() {
    let (dir, target) = write_sample(
        "use std::collections::HashMap;\nuse serde::{Serialize, Deserialize};"
    );
    let _ = dir;
    let analyzer = RustAnalyzer::new();
    let findings = analyzer.analyze(&target).unwrap();
    assert!(!findings.is_empty());
    let edges = &findings[0].edges;
    assert!(edges.is_some());
    let edges = edges.as_ref().unwrap();
    assert!(edges.iter().any(|e| e.name == "HashMap" && e.source.contains("collections")));
    assert!(edges.iter().any(|e| e.name == "Serialize"));
    assert!(edges.iter().any(|e| e.name == "Deserialize"));
}

#[test]
fn test_complexity_score_set() {
    let content = r#"
fn complex(x: i32) -> i32 {
    if x > 0 {
        match x {
            1 => 1,
            2 => 2,
            _ => 0,
        }
    } else {
        for i in 0..x {
            while i > 0 { i - 1; }
        }
    }
}
"#;
    let (dir, target) = write_sample(content);
    let _ = dir;
    let analyzer = RustAnalyzer::new();
    let findings = analyzer.analyze(&target).unwrap();
    assert!(!findings.is_empty());
    assert!(findings[0].complexity_score > 1);
}

#[test]
fn test_ignores_non_rust_files() {
    let dir = tempdir().unwrap();
    fs::write(dir.path().join("readme.md"), "# Not Rust").unwrap();
    let analyzer = RustAnalyzer::new();
    let findings = analyzer.analyze(dir.path()).unwrap();
    assert!(findings.is_empty());
}

#[test]
fn test_languages_includes_rs() {
    let analyzer = RustAnalyzer::new();
    assert!(analyzer.languages().contains(&".rs"));
}
