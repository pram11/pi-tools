use clap::{Parser, Subcommand};
use std::path::PathBuf;

#[derive(Parser)]
#[command(name = "kb")]
#[command(about = "Knowledge Base CRUD")]
pub struct App {
    #[command(subcommand)]
    pub command: Command,
}

#[derive(Subcommand)]
pub enum Command {
    /// Initialize the database
    Init,
    /// Index a file (chunk + embed + insert)
    Create {
        file_path: PathBuf,
        #[arg(short, long)]
        force: bool,
    },
    /// Search (hybrid vector + FTS5)
    Search {
        query: String,
        #[arg(short, long, default_value_t = 5)]
        top_k: usize,
        #[arg(long)]
        fuzzy: bool,
    },
    /// Update a file (delete old, re-insert)
    Update {
        file_path: PathBuf,
    },
    /// Delete by file/dir/pattern
    Delete {
        target: PathBuf,
        #[arg(long)]
        pattern: Option<String>,
    },
}
