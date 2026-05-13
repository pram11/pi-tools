//! Plugin registry.

use crate::analyzer::Analyzer;

mod jsx;
mod python;
mod regex;

pub use jsx::JsxAnalyzer;
pub use python::PythonAnalyzer;
pub use regex::RegexAnalyzer;

pub fn discover() -> Vec<Box<dyn Analyzer>> {
    vec![
        Box::new(PythonAnalyzer::new()),
        Box::new(JsxAnalyzer::new()),
        Box::new(RegexAnalyzer::new()),
    ]
}

pub fn filter_by_lang<'a>(
    plugins: &'a [Box<dyn Analyzer>],
    target_langs: &[String],
) -> Vec<&'a Box<dyn Analyzer>> {
    plugins
        .iter()
        .filter(|p| {
            target_langs.is_empty()
                || p.languages()
                    .iter()
                    .any(|lang| target_langs.iter().any(|tl| tl.contains(*lang)))
        })
        .collect()
}
