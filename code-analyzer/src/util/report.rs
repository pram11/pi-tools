//! E2E report builder.

use std::path::Path;

use chrono::Utc;

use crate::schema::{Finding, Report, ReportMetadata, Summary};

use crate::util::detector;

/// Wrap raw findings in a structured E2E report.
pub fn build_report(target: &Path, findings: &[Finding]) -> Report {
    let languages = detector::detect(target);
    let complexities: Vec<u32> = findings.iter().map(|f| f.complexity_score).collect();

    let summary = if complexities.is_empty() {
        Summary {
            avg_complexity: None,
            max_complexity: None,
            min_complexity: None,
        }
    } else {
        let sum: u64 = complexities.iter().map(|&c| c as u64).sum();
        let avg = sum as f64 / complexities.len() as f64;
        Summary {
            avg_complexity: Some((avg * 100.0).round() / 100.0),
            max_complexity: Some(*complexities.iter().max().unwrap()),
            min_complexity: Some(*complexities.iter().min().unwrap()),
        }
    };

    let unique_files: std::collections::HashSet<_> =
        findings.iter().map(|f| &f.file_path).collect();

    Report {
        metadata: ReportMetadata {
            target: target.canonicalize().map(|p| p.to_string_lossy().to_string()).unwrap_or_else(|_| target.to_string_lossy().to_string()),
            languages,
            total_files: unique_files.len(),
            total_findings: findings.len(),
            generated_at: Utc::now().to_rfc3339(),
        },
        findings: findings.to_vec(),
        summary,
    }
}
