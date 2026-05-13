use code_analyzer::util;
use tempfile::tempdir;

fn make_project(files: &[(&str, &str)]) -> std::path::PathBuf {
    let root = tempdir().unwrap();
    for (rel, content) in files {
        let path = root.path().join(rel);
        std::fs::create_dir_all(path.parent().unwrap()).unwrap();
        std::fs::write(&path, content).unwrap();
    }
    root.into_path()
}

fn analyze_and_report(root: &std::path::Path) -> code_analyzer::schema::Report {
    let findings = code_analyzer::analyze(root, None).unwrap();
    util::report::build_report(root, &findings)
}

#[test]
fn test_report_has_metadata() {
    let root = make_project(&[("app.py", "def f(): pass")]);
    let report = analyze_and_report(&root);
    assert!(!report.metadata.target.is_empty());
    assert!(!report.metadata.languages.is_empty());
    assert!(report.metadata.total_files > 0);
    assert!(report.metadata.total_findings > 0);
}

#[test]
fn test_report_findings_mirrors_analysis() {
    let root = make_project(&[
        ("a.py", "def x(): pass"),
        ("b.py", "class C: pass"),
    ]);
    let findings = code_analyzer::analyze(&root, None).unwrap();
    let report = analyze_and_report(&root);
    assert_eq!(report.findings.len(), findings.len());
}

#[test]
fn test_report_summary_has_complexity_stats() {
    let root = make_project(&[("app.py", "def f(): pass\nif True: pass")]);
    let report = analyze_and_report(&root);
    assert!(report.summary.avg_complexity.is_some());
    assert!(report.summary.max_complexity.is_some());
    assert!(report.summary.min_complexity.is_some());
}

#[test]
fn test_report_json_dumps() {
    let root = make_project(&[("app.py", "pass")]);
    let report = analyze_and_report(&root);
    let text = serde_json::to_string(&report).unwrap();
    assert!(text.contains("metadata"));
}

#[test]
fn test_report_detects_languages() {
    let root = make_project(&[
        ("requirements.txt", "flask"),
        ("app.py", "pass"),
    ]);
    let report = analyze_and_report(&root);
    assert!(report.metadata.languages.contains(&"python".to_string()));
}
