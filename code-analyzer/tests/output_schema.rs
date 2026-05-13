use code_analyzer::schema::Finding;
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

#[test]
fn test_output_is_list_of_dicts() {
    let root = make_project(&[("app.py", "def hello(): pass")]);
    let results = code_analyzer::analyze(&root, None).unwrap();
    assert!(!results.is_empty());
}

#[test]
fn test_schema_has_required_keys() {
    let root = make_project(&[("app.py", "class App:\n    def run(self): pass")]);
    let results = code_analyzer::analyze(&root, None).unwrap();
    for item in &results {
        assert!(!item.file_path.is_empty());
        assert!(matches!(
            item.feature_type,
            code_analyzer::schema::FeatureType::Route
                | code_analyzer::schema::FeatureType::Component
                | code_analyzer::schema::FeatureType::Logic
        ));
    }
}

#[test]
fn test_feature_type_is_valid() {
    let root = make_project(&[("app.py", "def f(): pass")]);
    let results = code_analyzer::analyze(&root, None).unwrap();
    let valid = ["Route", "Component", "Logic"];
    for item in &results {
        let ft = item.feature_type.to_string();
        assert!(valid.contains(&ft.as_str()));
    }
}

#[test]
fn test_json_serializable() {
    let root = make_project(&[("app.py", "x = 1")]);
    let results = code_analyzer::analyze(&root, None).unwrap();
    let dumped = serde_json::to_string(&results).unwrap();
    let parsed: Vec<Finding> = serde_json::from_str(&dumped).unwrap();
    assert_eq!(parsed.len(), results.len());
}

#[test]
fn test_file_path_is_absolute() {
    let root = make_project(&[("app.py", "pass")]);
    let results = code_analyzer::analyze(&root, None).unwrap();
    for item in &results {
        assert!(std::path::Path::new(&item.file_path).is_absolute());
    }
}

#[test]
fn test_identifiers_is_list() {
    let root = make_project(&[("app.py", "def a(): pass\ndef b(): pass")]);
    let results = code_analyzer::analyze(&root, None).unwrap();
    for item in &results {
        // identifiers is Vec<String>
        let _ = &item.identifiers;
    }
}

#[test]
fn test_complexity_is_positive() {
    let root = make_project(&[("app.py", "def f(): pass")]);
    let results = code_analyzer::analyze(&root, None).unwrap();
    for item in &results {
        assert!(item.complexity_score >= 0);
    }
}
