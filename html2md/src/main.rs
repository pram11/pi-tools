use std::io::{self, Read};
use std::process;

use clap::{CommandFactory, Parser};

use html2md::engine;

#[derive(Parser, Debug)]
#[command(name = "html2md", about = "Convert HTML to Markdown")]
struct Args {
    /// Local HTML file path
    #[arg(long)]
    file: Option<String>,

    /// Inline HTML string
    #[arg(long)]
    html: Option<String>,

    /// Write Markdown to file (default: stdout)
    #[arg(long)]
    output: Option<String>,

    /// Converter backend
    #[arg(long, default_value = "comrak")]
    backend: String,

    /// Omit <img> tags
    #[arg(long)]
    strip_images: bool,

    /// Omit <a> tags
    #[arg(long)]
    strip_links: bool,

    /// Line wrap width (0 = no wrap)
    #[arg(long, default_value = "0")]
    wrap: usize,
}

fn main() {
    let args = Args::parse();

    // --- resolve input ---
    let html = if let Some(ref path) = args.file {
        std::fs::read_to_string(path).unwrap_or_else(|e| {
            eprintln!("Error: file not found: {path}: {e}");
            process::exit(1);
        })
    } else if let Some(ref s) = args.html {
        s.clone()
    } else if atty::is(atty::Stream::Stdin) {
        let _ = Args::command().print_help();
        eprintln!();
        process::exit(1);
    } else {
        let mut buf = String::new();
        io::stdin().read_to_string(&mut buf).unwrap_or_else(|e| {
            eprintln!("Error: {e}");
            process::exit(1);
        });
        if buf.trim().is_empty() {
            eprintln!("Error: no input provided. Use --file, --html, or pipe via stdin.");
            process::exit(1);
        }
        buf
    };

    // --- convert ---
    let md = match engine::convert(&html, &args.backend) {
        Ok(m) => m,
        Err(e) => {
            eprintln!("Error: {e}");
            process::exit(1);
        }
    };

    // --- post-filter ---
    let md = apply_filters(md, &args);

    // --- wrap ---
    let md = if args.wrap > 0 {
        wrap_lines(&md, args.wrap)
    } else {
        md
    };

    // --- output ---
    if let Some(out_path) = args.output {
        std::fs::write(&out_path, &md).unwrap_or_else(|e| {
            eprintln!("Error writing output: {e}");
            process::exit(1);
        });
        eprintln!("→ {out_path}");
    } else {
        print!("{md}");
    }
}

fn apply_filters(md: String, args: &Args) -> String {
    let mut result = md;
    if args.strip_images {
        // Remove ![alt](src) patterns
        result = regex::Regex::new(r"\!\[.*?\]\(.*?\)")
            .unwrap()
            .replace_all(&result, "")
            .to_string();
    }
    if args.strip_links {
        // Remove [text](url) → text
        result = regex::Regex::new(r"\[(.*?)\]\(.*?\)")
            .unwrap()
            .replace_all(&result, "$1")
            .to_string();
    }
    result
}

fn wrap_lines(md: &str, width: usize) -> String {
    let mut wrapped = Vec::new();
    for line in md.lines() {
        if line.trim().is_empty()
            || line.starts_with('#')
            || line.starts_with('-')
            || line.starts_with('|')
            || line.starts_with('>')
        {
            wrapped.push(line.to_string());
        } else if line.len() > width {
            wrapped.extend(word_wrap(line, width));
        } else {
            wrapped.push(line.to_string());
        }
    }
    wrapped.join("\n")
}

fn word_wrap(line: &str, width: usize) -> Vec<String> {
    let mut lines = Vec::new();
    for chunk in line.split_whitespace() {
        if lines.is_empty() {
            lines.push(chunk.to_string());
            continue;
        }
        let last = lines.last_mut().unwrap();
        if last.len() + 1 + chunk.len() <= width {
            last.push(' ');
            last.push_str(chunk);
        } else {
            lines.push(chunk.to_string());
        }
    }
    lines
}
