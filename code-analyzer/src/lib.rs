//! Code-Analyzer library.

pub mod analyzer;
pub mod analyzers;
pub mod schema;

pub mod util;

/// Run all analyzers on `target`, returning merged findings.
pub fn analyze(
    target: &std::path::Path,
    lang_filter: Option<&[String]>,
) -> Result<Vec<schema::Finding>, analyzer::Error> {
    let plugins = analyzers::discover();
    let langs: Vec<String> = lang_filter.unwrap_or_default().to_vec();
    let active = analyzers::filter_by_lang(&plugins, &langs);
    let mut findings = Vec::new();
    for plugin in active {
        findings.extend(plugin.analyze(target)?);
    }
    Ok(findings)
}
