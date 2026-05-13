use code_analyzer::analyzers;
use code_analyzer::analyzer::Analyzer;

#[test]
fn test_discovers_at_least_one_plugin() {
    let plugins = analyzers::discover();
    assert!(plugins.len() >= 1);
}

#[test]
fn test_plugins_declare_languages() {
    let plugins = analyzers::discover();
    for p in &plugins {
        assert!(!p.languages().is_empty());
    }
}

#[test]
fn test_plugins_have_analyze_method() {
    let plugins = analyzers::discover();
    // Just check they compile — trait enforces the method
    assert!(!plugins.is_empty());
}

#[test]
fn test_filter_by_lang() {
    let plugins = analyzers::discover();
    let py = analyzers::filter_by_lang(&plugins, &[String::from(".py")]);
    assert!(!py.is_empty());
    let none = analyzers::filter_by_lang(&plugins, &[String::from(".xyz")]);
    assert!(none.is_empty());
    let all = analyzers::filter_by_lang(&plugins, &[]);
    assert_eq!(all.len(), plugins.len());
}
