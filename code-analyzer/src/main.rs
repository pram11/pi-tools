//! Code-Analyzer CLI — static analysis entry point.

use std::path::PathBuf;

use anyhow::Result;
use clap::Parser as ClapParser;

mod analyzer;
mod analyzers;
mod schema;

mod util;

use analyzers::{filter_by_lang, discover};

#[derive(ClapParser, Debug)]
#[command(name = "code-analyzer", about = "Deep static analysis for feature chart generation")]
struct Cli {
    /// Target directory or file to analyze
    #[arg(short, long, default_value = ".")]
    path: PathBuf,

    /// Comma-separated language filter (e.g. ".py,.tsx")
    #[arg(short, long)]
    lang: Option<String>,

    /// Condense output for LLM context windows
    #[arg(short, long, default_value_t = false)]
    condensed: bool,
}

fn run(cli: &Cli) -> Result<()> {
    let target = cli.path.canonicalize().unwrap_or_else(|_| cli.path.clone());
    if !target.exists() {
        anyhow::bail!("Path not found: {}", target.display());
    }

    let plugins = discover();
    let target_langs: Vec<String> = cli
        .lang
        .as_ref()
        .map(|l| l.split(',').map(|s| s.trim().to_string()).collect())
        .unwrap_or_default();

    let active = filter_by_lang(&plugins, &target_langs);
    if active.is_empty() {
        anyhow::bail!("No analyzers match the requested languages");
    }

    let mut findings = Vec::new();
    for plugin in active {
        match plugin.analyze(&target) {
            Ok(f) => findings.extend(f),
            Err(e) => eprintln!("[WARN] Analyzer failed: {e}"),
        }
    }

    let report = util::report::build_report(&target, &findings);

    let output = if cli.condensed {
        serde_json::to_string_pretty(&util::condense::condense_report(&report))
    } else {
        serde_json::to_string_pretty(&report)
    }?;

    println!("{output}");
    Ok(())
}

fn main() -> Result<()> {
    let cli = Cli::parse();
    run(&cli)
}
