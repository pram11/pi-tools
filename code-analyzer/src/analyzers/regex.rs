//! RegexAnalyzer — fallback multi-language file discovery.

use std::path::Path;

use crate::analyzer::Analyzer;
use crate::schema::{Finding, FeatureType};
use crate::util::filter;

pub struct RegexAnalyzer;

impl RegexAnalyzer {
    pub fn new() -> Self {
        Self
    }
}

impl Analyzer for RegexAnalyzer {
    fn languages(&self) -> &[&str] {
        &[".py", ".java", ".go", ".rs", ".rb", ".c", ".cpp", ".h"]
    }

    fn analyze(&self, target: &Path) -> Result<Vec<Finding>, crate::analyzer::Error> {
        let mut results = Vec::new();
        let target = target.canonicalize().unwrap_or_else(|_| target.to_path_buf());

        let files = if target.is_file() {
            if self.languages().iter().any(|l| {
                target.extension().map_or(false, |e| format!(".{}", e.to_string_lossy()) == *l)
            }) {
                vec![target]
            } else {
                vec![]
            }
        } else {
            filter::iter_sources(&target, self.languages(), None)
        };

        for f in files {
            results.push(Finding {
                file_path: f.to_string_lossy().to_string(),
                feature_type: FeatureType::Logic,
                identifiers: Vec::new(),
                complexity_score: 0,
                loc: None,
                nesting_depth: None,
                routes: None,
                edges: None,
            });
        }

        Ok(results)
    }
}
