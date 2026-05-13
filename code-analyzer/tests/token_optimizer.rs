use code_analyzer::schema::*;
use code_analyzer::util::condense;

fn sample_report(count: usize) -> Report {
    let findings: Vec<Finding> = (0..count)
        .map(|i| Finding {
            file_path: format!("/src/mod{i}.py"),
            feature_type: FeatureType::Logic,
            identifiers: vec![format!("func_{i}")],
            complexity_score: (i + 1) as u32,
            loc: None,
            nesting_depth: None,
            routes: None,
            edges: None,
        })
        .collect();
    Report {
        metadata: ReportMetadata {
            target: "/src".to_string(),
            languages: vec!["python".to_string()],
            total_files: count,
            total_findings: count,
            generated_at: "2025-01-01T00:00:00+00:00".to_string(),
        },
        findings,
        summary: Summary {
            avg_complexity: Some(5.5),
            max_complexity: Some(11),
            min_complexity: Some(1),
        },
    }
}

#[test]
fn test_condensed_is_shorter() {
    let report = sample_report(20);
    let full_len = serde_json::to_string(&report).unwrap().len();
    let condensed = condense::condense_report(&report);
    let short_len = serde_json::to_string(&condensed).unwrap().len();
    assert!(short_len < full_len, "No savings: {short_len} vs {full_len}");
}

#[test]
fn test_condensed_groups_by_feature_type() {
    let report = sample_report(5);
    let condensed = condense::condense_report(&report);
    assert!(condensed.grouped.contains_key("Logic"));
}

#[test]
fn test_condensed_preserves_metadata() {
    let report = sample_report(1);
    let condensed = condense::condense_report(&report);
    assert_eq!(condensed.metadata.target, "/src");
    assert_eq!(condensed.metadata.languages, vec!["python"]);
}

#[test]
fn test_condensed_merges_identifiers() {
    let report = sample_report(3);
    let condensed = condense::condense_report(&report);
    let logic = &condensed.grouped["Logic"];
    assert_eq!(logic.identifiers.len(), 3);
    assert!(logic.identifiers.contains(&"func_0".to_string()));
    assert!(logic.identifiers.contains(&"func_1".to_string()));
}

#[test]
fn test_condensed_keeps_summary() {
    let report = sample_report(4);
    let condensed = condense::condense_report(&report);
    assert_eq!(condensed.summary.avg, Some(5.5));
    assert_eq!(condensed.summary.max, Some(11));
}

#[test]
fn test_condensed_uses_relative_paths() {
    let report = sample_report(2);
    let condensed = condense::condense_report(&report);
    let logic = &condensed.grouped["Logic"];
    for p in &logic.files {
        assert!(!p.starts_with('/'), "Path should be relative: {p}");
    }
}

#[test]
fn test_empty_report_no_crash() {
    let empty = Report {
        metadata: ReportMetadata {
            target: "".to_string(),
            languages: vec![],
            total_files: 0,
            total_findings: 0,
            generated_at: "".to_string(),
        },
        findings: vec![],
        summary: Summary {
            avg_complexity: None,
            max_complexity: None,
            min_complexity: None,
        },
    };
    let condensed = condense::condense_report(&empty);
    assert!(condensed.grouped.is_empty());
    assert_eq!(condensed.total_files, 0);
}
