//! ProjectDetector — heuristic project type identification.

use std::collections::HashSet;
use std::path::Path;

const SIGNATURES: &[(&str, &[&str])] = &[
    ("python", &["requirements.txt", "setup.py", "setup.cfg", "pyproject.toml", "Pipfile"]),
    ("javascript", &["package.json", "yarn.lock", "package-lock.json"]),
    ("typescript", &["tsconfig.json"]),
    ("nextjs", &["next.config.js", "next.config.mjs", "next.config.ts"]),
    ("java", &["pom.xml", "build.gradle", "build.gradle.kts"]),
    ("rust", &["Cargo.toml", "Cargo.lock"]),
    ("go", &["go.mod", "go.sum"]),
    ("ruby", &["Gemfile", "Gemfile.lock"]),
    ("dotnet", &["csproj", "sln", "fsproj"]),
];

const EXT_MAP: &[(&str, &str)] = &[
    (".py", "python"),
    (".js", "javascript"),
    (".ts", "typescript"),
    (".tsx", "typescript"),
    (".jsx", "javascript"),
    (".java", "java"),
    (".rs", "rust"),
    (".go", "go"),
    (".rb", "ruby"),
];

pub fn detect(target: &Path) -> Vec<String> {
    let target = target.canonicalize().unwrap_or_else(|_| target.to_path_buf());
    if !target.is_dir() {
        return vec!["unknown".to_string()];
    }

    let mut detected = Vec::new();

    let marker_names: HashSet<String> = target
        .read_dir()
        .ok()
        .into_iter()
        .flat_map(|r| r)
        .filter_map(|e| e.ok())
        .filter(|e| e.file_type().ok().map(|t| t.is_file()).unwrap_or(false))
        .map(|e| e.file_name().to_string_lossy().to_lowercase())
        .collect();

    for (lang, markers) in SIGNATURES {
        let marker_set: HashSet<_> = markers.iter().map(|s| s.to_lowercase()).collect();
        if marker_set.intersection(&marker_names).next().is_some() {
            detected.push(lang.to_string());
        }
    }

    if detected.is_empty() {
        let mut exts = HashSet::new();
        for entry in walkdir::WalkDir::new(&target).into_iter().filter_map(|e| e.ok()) {
            let path = entry.path();
            if path.is_file() {
                if let Some(ext) = path.extension().and_then(|e| e.to_str()) {
                    exts.insert(format!(".{ext}").to_lowercase());
                }
            }
        }

        let mut langs = HashSet::new();
        for (ext, lang) in EXT_MAP {
            if exts.contains(*ext) {
                langs.insert(*lang);
            }
        }
        detected = langs.into_iter().map(|s| s.to_string()).collect();
        detected.sort();
    }

    if detected.is_empty() {
        detected.push("unknown".to_string());
    }

    detected
}
