//! Token optimizer — condense analysis report for LLM context windows.

use std::collections::{HashMap, HashSet};
use std::path::{Path, PathBuf};

use crate::schema::{CondensedMetadata, CondensedReport, CondensedSummary, FeatureGroup, Report};

pub fn condense_report(report: &Report) -> CondensedReport {
    if report.findings.is_empty() {
        return CondensedReport {
            metadata: CondensedMetadata {
                target: report.metadata.target.clone(),
                languages: report.metadata.languages.clone(),
            },
            grouped: HashMap::new(),
            summary: CondensedSummary {
                avg: report.summary.avg_complexity,
                max: report.summary.max_complexity,
                min: report.summary.min_complexity,
            },
            total_files: 0,
        };
    }

    let target = PathBuf::from(&report.metadata.target);
    let mut grouped: HashMap<String, (Vec<String>, HashSet<String>)> = HashMap::new();

    for f in &report.findings {
        let ft = f.feature_type.to_string();
        let entry = grouped.entry(ft).or_insert_with(|| (Vec::new(), HashSet::new()));
        entry.0.extend(f.identifiers.clone());
        let path = Path::new(&f.file_path);
        match path.strip_prefix(&target) {
            Ok(rel) => {
                entry.1.insert(rel.to_string_lossy().to_string());
            }
            Err(_) => {
                entry.1.insert(f.file_path.clone());
            }
        }
    }

    let grouped_map: HashMap<String, FeatureGroup> = grouped
        .into_iter()
        .map(|(ft, (ids, files))| {
            let ids: Vec<_> = ids.into_iter().collect::<HashSet<_>>().into_iter().collect();
            let mut files = files.into_iter().collect::<Vec<_>>();
            files.sort();
            (ft, FeatureGroup { identifiers: ids, files })
        })
        .collect();

    let mut all_files = HashSet::new();
    for g in grouped_map.values() {
        all_files.extend(g.files.iter().cloned());
    }

    CondensedReport {
        metadata: CondensedMetadata {
            target: report.metadata.target.clone(),
            languages: report.metadata.languages.clone(),
        },
        grouped: grouped_map,
        summary: CondensedSummary {
            avg: report.summary.avg_complexity,
            max: report.summary.max_complexity,
            min: report.summary.min_complexity,
        },
        total_files: all_files.len(),
    }
}
