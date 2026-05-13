use code_analyzer::util::detector;
use tempfile::tempdir;

fn make_project(files: &[(&str, &str)]) -> std::path::PathBuf {
    let root = tempdir().unwrap();
    for (rel, content) in files {
        std::fs::write(root.path().join(rel), content).unwrap();
    }
    root.into_path()
}

#[test]
fn test_detects_python_project() {
    let root = make_project(&[
        ("requirements.txt", "flask"),
        ("app.py", ""),
    ]);
    let info = detector::detect(&root);
    assert!(info.contains(&"python".to_string()));
}

#[test]
fn test_detects_node_project() {
    let root = make_project(&[("package.json", "{}"), ("index.js", "")]);
    let info = detector::detect(&root);
    assert!(
        info.contains(&"javascript".to_string()),
        "Expected javascript, got: {:?}",
        info
    );
}

#[test]
fn test_detects_java_project() {
    let root = make_project(&[("pom.xml", "<project/>"), ("App.java", "")]);
    let info = detector::detect(&root);
    assert!(info.contains(&"java".to_string()));
}

#[test]
fn test_detects_mixed_project() {
    let root =
        make_project(&[("requirements.txt", ""), ("package.json", "{}")]);
    let info = detector::detect(&root);
    assert!(info.len() >= 2);
}

#[test]
fn test_empty_dir_returns_unknown() {
    let root = tempdir().unwrap().into_path();
    let info = detector::detect(&root);
    assert!(info.contains(&"unknown".to_string()));
}
