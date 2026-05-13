//! Shared file filtering utilities.

use std::path::Path;

const DEFAULT_EXCLUDE_DIRS: &[&str] = &[
    ".venv", "__pycache__", ".git", "node_modules", ".pytest_cache",
    ".mypy_cache", ".tox", "venv", "env", "dist", "build", ".eggs",
    "target", ".cargo",
];

fn should_exclude(path: &Path, exclude_dirs: Option<&[String]>) -> bool {
    let dirs: Vec<&str> = if let Some(ex) = exclude_dirs {
        ex.iter().map(|s| s.as_str()).collect()
    } else {
        DEFAULT_EXCLUDE_DIRS.to_vec()
    };

    for component in path.components() {
        let name = component.as_os_str().to_string_lossy();
        for pattern in &dirs {
            if name == *pattern {
                return true;
            }
            if pattern.starts_with('*') && name.ends_with(&pattern[1..]) {
                return true;
            }
        }
    }
    false
}

pub fn iter_sources(
    root: &Path,
    extensions: &[&str],
    exclude_dirs: Option<&[String]>,
) -> Vec<std::path::PathBuf> {
    let mut results = Vec::new();
    if !root.is_dir() {
        return results;
    }

    for entry in walkdir::WalkDir::new(root)
        .into_iter()
        .filter_entry(|e| !should_exclude(e.path(), exclude_dirs))
    {
        let entry = match entry {
            Ok(e) => e,
            Err(_) => continue,
        };
        let path = entry.path();
        if !path.is_file() {
            continue;
        }
        if let Some(ext) = path.extension().and_then(|e| e.to_str()) {
            let full_ext = format!(".{ext}");
            if extensions.iter().any(|e| *e == full_ext) {
                results.push(path.to_path_buf());
            }
        }
    }

    results.sort();
    results
}
