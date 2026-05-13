//! JSXAnalyzer — tree-sitter-typescript based TSX/JSX source mapping.

use std::collections::HashSet;
use std::path::Path;
use std::sync::Mutex;

use tree_sitter::{Language, Node};

use crate::analyzer::{Analyzer, Error};
use crate::util::filter;
use crate::schema::{Edge, FeatureType, Finding};

fn tsx_language() -> Language {
    tree_sitter_typescript::language_tsx()
}

const ROUTE_FILES: &[&str] =
    &["page.tsx", "layout.tsx", "loading.tsx", "error.tsx", "not-found.tsx", "route.ts"];

pub struct JsxAnalyzer {
    parser: Mutex<tree_sitter::Parser>,
}

impl JsxAnalyzer {
    pub fn new() -> Self {
        let mut p = tree_sitter::Parser::new();
        p.set_language(&tsx_language()).expect("tree-sitter-typescript");
        Self { parser: Mutex::new(p) }
    }

    fn get_route_path(&self, path: &Path, base: &Path) -> Option<String> {
        for sub in &["app", "src/app"] {
            if let Ok(rel) = path.strip_prefix(base.join(sub)) {
                let name = rel.file_name().and_then(|n| n.to_str());
                if name.map_or(false, |n| ROUTE_FILES.contains(&n)) {
                    let parts: Vec<_> = rel
                        .components()
                        .filter(|c| {
                            let nm = c.as_os_str().to_string_lossy();
                            !ROUTE_FILES.contains(&nm.as_ref())
                        })
                        .map(|c| c.as_os_str().to_string_lossy().to_string())
                        .collect();
                    return Some(if parts.is_empty() {
                        "/".to_string()
                    } else {
                        format!("/{}", parts.join("/"))
                    });
                }
            }
        }
        None
    }

    fn extract_imports(&self, node: Node, src: &[u8]) -> Vec<(String, String)> {
        let mut imports = Vec::new();
        for child in node.named_children(&mut node.walk()) {
            if child.kind() == "import_statement" {
                let source = child
                    .child_by_field_name("source")
                    .and_then(|n| n.utf8_text(src).ok())
                    .map(|s| s.trim_matches(|c: char| c == '"' || c == '\'').to_string());
                if let Some(source_str) = source {
                    for c in child.named_children(&mut child.walk()) {
                        if c.kind() == "import_clause" {
                            for gc in c.named_children(&mut c.walk()) {
                                if gc.kind() == "identifier" {
                                    if let Ok(name) = gc.utf8_text(src) {
                                        imports.push((name.to_string(), source_str.clone()));
                                    }
                                } else if gc.kind() == "named_imports" {
                                    for s in gc.named_children(&mut gc.walk()) {
                                        if s.kind() == "import_specifier" {
                                            if let Some(id) = s.named_child(0) {
                                                if id.kind() == "identifier" {
                                                    if let Ok(name) = id.utf8_text(src) {
                                                        imports
                                                            .push((name.to_string(), source_str.clone()));
                                                    }
                                                }
                                            }
                                        } else if s.kind() == "namespace_import" {
                                            if let Some(id) = s.named_child(0) {
                                                if id.kind() == "identifier" {
                                                    if let Ok(name) = id.utf8_text(src) {
                                                        imports
                                                            .push((name.to_string(), source_str.clone()));
                                                    }
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
        imports
    }

    fn is_pascal_case(name: &str) -> bool {
        !name.is_empty()
            && name.chars().next().map_or(false, |c| c.is_uppercase())
            && !name.starts_with("use")
    }

    fn is_hook(name: &str) -> bool {
        name.starts_with("use")
            && name.len() > 3
            && name.chars().nth(3).map_or(false, |c| c.is_uppercase())
    }

    fn find_identifiers(node: Node, src: &[u8], seen: &mut HashSet<String>) -> Vec<String> {
        let mut results = Vec::new();
        match node.kind() {
            "function_declaration" | "class_declaration" => {
                for c in node.named_children(&mut node.walk()) {
                    if c.kind() == "identifier" {
                        if let Ok(name) = c.utf8_text(src) {
                            let s = name.to_string();
                            if seen.insert(s.clone()) {
                                results.push(s);
                            }
                        }
                        break;
                    }
                }
            }
            "lexical_declaration" | "variable_declaration" => {
                for c in node.named_children(&mut node.walk()) {
                    if c.kind() == "variable_declarator" {
                        for gc in c.named_children(&mut c.walk()) {
                            if gc.kind() == "identifier" {
                                if let Ok(name) = gc.utf8_text(src) {
                                    let s = name.to_string();
                                    if (Self::is_pascal_case(&s) || Self::is_hook(&s))
                                        && seen.insert(s.clone())
                                    {
                                        results.push(s);
                                    }
                                }
                                break;
                            }
                        }
                    }
                }
            }
            "interface_declaration" | "type_alias_declaration" => {
                for c in node.named_children(&mut node.walk()) {
                    if c.kind() == "type_identifier" || c.kind() == "identifier" {
                        if let Ok(name) = c.utf8_text(src) {
                            let s = name.to_string();
                            if seen.insert(s.clone()) {
                                results.push(s);
                            }
                        }
                        break;
                    }
                }
            }
            _ => {}
        }
        results
    }

    fn walk_exports(node: Node, src: &[u8], seen: &mut HashSet<String>) -> Vec<String> {
        let mut results = Vec::new();
        for c in node.named_children(&mut node.walk()) {
            if c.kind() == "export_statement" {
                for gc in c.named_children(&mut c.walk()) {
                    results.extend(Self::find_identifiers(gc, src, seen));
                }
            } else {
                results.extend(Self::find_identifiers(c, src, seen));
            }
        }
        results
    }

    fn count_complexity(node: Node) -> u32 {
        let branch_types = [
            "if_statement", "else_clause", "for_statement", "for_in_statement",
            "while_statement", "do_statement", "switch_statement", "case_statement",
            "catch_clause", "conditional_expression", "logical_or_expression",
            "logical_and_expression",
        ];
        let mut score: u32 = 0;
        for c in node.named_children(&mut node.walk()) {
            if branch_types.contains(&c.kind()) {
                score += 1;
            }
            score += Self::count_complexity(c);
        }
        score
    }

    fn count_loc(source: &str) -> usize {
        source.trim().lines().count()
    }

    fn max_nesting(node: Node, depth: usize) -> usize {
        let nesting = ["statement_block", "jsx_element", "jsx_self_closing_element"];
        let mut max_d = depth;
        for c in node.named_children(&mut node.walk()) {
            let d = if nesting.contains(&c.kind()) { depth + 1 } else { depth };
            max_d = max_d.max(Self::max_nesting(c, d));
        }
        max_d
    }

    fn analyze_file(&self, fpath: &Path, base: &Path) -> Option<Finding> {
        let source = std::fs::read(fpath).ok()?;
        let source_str = String::from_utf8_lossy(&source);
        let mut parser = self.parser.lock().unwrap();
        let tree = parser.parse(&source, None)?;
        let root = tree.root_node();

        let mut seen: HashSet<String> = HashSet::new();
        let identifiers = Self::walk_exports(root, &source, &mut seen);
        let imports = self.extract_imports(root, &source);
        let edges: Vec<Edge> = imports
            .into_iter()
            .map(|(n, m)| Edge {
                edge_type: "import".to_string(),
                name: n,
                source: m,
            })
            .collect();
        let routes = self.get_route_path(fpath, base).map(|r| vec![r]);
        let complexity = Self::count_complexity(root);
        let loc = Self::count_loc(&source_str);
        let nesting_depth = Self::max_nesting(root, 0);

        let feature_type = if routes.is_some() {
            FeatureType::Route
        } else if identifiers.iter().any(|s| Self::is_pascal_case(s)) {
            FeatureType::Component
        } else {
            FeatureType::Logic
        };

        Some(Finding {
            file_path: fpath.to_string_lossy().to_string(),
            feature_type,
            identifiers,
            complexity_score: complexity,
            loc: Some(loc),
            nesting_depth: Some(nesting_depth),
            routes,
            edges: if edges.is_empty() { None } else { Some(edges) },
        })
    }
}

impl Analyzer for JsxAnalyzer {
    fn languages(&self) -> &[&str] {
        &[".tsx", ".jsx"]
    }

    fn analyze(&self, target: &Path) -> Result<Vec<Finding>, Error> {
        let mut results = Vec::new();
        let target_resolved = target.canonicalize().unwrap_or_else(|_| target.to_path_buf());

        let files = if target_resolved.is_file() {
            if self.languages().iter().any(|l| {
                target_resolved.extension()
                    .map_or(false, |e| format!(".{}", e.to_string_lossy()) == *l)
            }) {
                vec![target_resolved.clone()]
            } else {
                vec![]
            }
        } else {
            filter::iter_sources(&target_resolved, self.languages(), None)
        };

        for f in files {
            if let Some(entry) = self.analyze_file(&f, &target_resolved) {
                results.push(entry);
            }
        }

        Ok(results)
    }
}
