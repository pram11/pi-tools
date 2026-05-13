//! PythonAnalyzer — tree-sitter-python based source mapping.

use std::path::Path;
use std::sync::Mutex;

use tree_sitter::{Language, Node};

use crate::analyzer::{Analyzer, Error};
use crate::schema::{Finding, FeatureType};
use crate::util::filter;

fn python_language() -> Language {
    tree_sitter_python::language()
}

pub struct PythonAnalyzer {
    parser: Mutex<tree_sitter::Parser>,
}

impl PythonAnalyzer {
    pub fn new() -> Self {
        let mut p = tree_sitter::Parser::new();
        p.set_language(&python_language()).expect("tree-sitter-python");
        Self { parser: Mutex::new(p) }
    }

    fn walk_node(&self, node: Node, source: &[u8], items: &mut Vec<(String, FeatureType)>) {
        let node_type = node.kind();

        if node_type == "function_definition" || node_type == "async_function_definition" {
            if let Some(name_node) = node.child_by_field_name("name") {
                if let Ok(text) = name_node.utf8_text(source) {
                    items.push((text.to_string(), FeatureType::Logic));
                }
            }
        }

        if node_type == "class_definition" {
            if let Some(name_node) = node.child_by_field_name("name") {
                if let Ok(text) = name_node.utf8_text(source) {
                    items.push((text.to_string(), FeatureType::Component));
                    let class_name = text.to_string();
                    if let Some(body) = node.child_by_field_name("body") {
                        let mut nested = Vec::new();
                        self.walk_node(body, source, &mut nested);
                        for (name, _) in nested {
                            items.push((format!("{class_name}.{name}"), FeatureType::Logic));
                        }
                    }
                }
            }
        }

        let mut child = node.named_child(0);
        while let Some(c) = child {
            if node_type != "class_definition" || c.kind() != "body" {
                self.walk_node(c, source, items);
            }
            child = c.next_named_sibling();
        }
    }

    fn walk_ast(&self, node: Node, source: &[u8]) -> Vec<(String, FeatureType)> {
        let mut items = Vec::new();
        self.walk_node(node, source, &mut items);
        items
    }

    fn count_complexity(&self, node: Node) -> u32 {
        let mut score: u32 = 1;
        let mut stack = vec![node];
        while let Some(current) = stack.pop() {
            match current.kind() {
                "if_statement" | "for_statement" | "while_statement"
                | "except_clause" | "assert_statement" => {
                    score += 1;
                }
                _ => {}
            }
            let mut child = current.named_child(0);
            while let Some(c) = child {
                stack.push(c);
                child = c.next_named_sibling();
            }
        }
        score
    }
}

impl Analyzer for PythonAnalyzer {
    fn languages(&self) -> &[&str] {
        &[".py"]
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
            let source = std::fs::read(&f).map_err(|e| Error::Io(e))?;
            let mut parser = self.parser.lock().unwrap();
            let tree = match parser.parse(&source, None) {
                Some(t) => t,
                None => continue,
            };

            let root = tree.root_node();
            let items = self.walk_ast(root, &source);
            let complexity = self.count_complexity(root);

            if items.is_empty() {
                continue;
            }

            results.push(Finding {
                file_path: f.to_string_lossy().to_string(),
                feature_type: FeatureType::Logic,
                identifiers: items.into_iter().map(|(n, _)| n).collect(),
                complexity_score: complexity,
                loc: None,
                nesting_depth: None,
                routes: None,
                edges: None,
            });
        }

        Ok(results)
    }
}
