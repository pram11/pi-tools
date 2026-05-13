//! RustAnalyzer — tree-sitter-rust based source mapping.

use std::path::Path;
use std::sync::Mutex;

use tree_sitter::Node;

use crate::analyzer::{Analyzer, Error};
use crate::schema::{Edge, FeatureType, Finding};
use crate::util::filter;

fn rust_language() -> tree_sitter::Language {
    tree_sitter_rust::language()
}

pub struct RustAnalyzer {
    parser: Mutex<tree_sitter::Parser>,
}

impl RustAnalyzer {
    pub fn new() -> Self {
        let mut p = tree_sitter::Parser::new();
        p.set_language(&rust_language()).expect("tree-sitter-rust");
        Self { parser: Mutex::new(p) }
    }

    /// Extract (identifier, FeatureType) pairs from AST.
    fn walk_ast(&self, node: Node, source: &[u8]) -> Vec<(String, FeatureType)> {
        let mut items = Vec::new();
        self.walk_node(node, source, &mut items, None);
        items
    }

    fn walk_node(
        &self,
        node: Node,
        source: &[u8],
        items: &mut Vec<(String, FeatureType)>,
        parent_name: Option<&str>,
    ) {
        match node.kind() {
            "function_item" => {
                if let Some(name) = self.get_func_name(node, source) {
                    let ident = match parent_name {
                        Some(parent) => format!("{}.{}", parent, name),
                        None => name,
                    };
                    items.push((ident, FeatureType::Logic));
                }
            }
            "struct_item" => {
                if let Some(name) = self.get_type_name(node, source) {
                    items.push((name, FeatureType::Component));
                }
                // recurse for nested items
                let mut child = node.named_child(0);
                while let Some(c) = child {
                    self.walk_node(c, source, items, parent_name);
                    child = c.next_named_sibling();
                }
                return;
            }
            "enum_item" => {
                if let Some(name) = self.get_type_name(node, source) {
                    items.push((name.clone(), FeatureType::Component));
                    // Extract variant names
                    let mut child = node.named_child(0);
                    while let Some(c) = child {
                        if c.kind() == "enum_variant_list" {
                            let mut vc = c.named_child(0);
                            while let Some(v) = vc {
                                if v.kind() == "enum_variant" {
                                    if let Some(var_name) = v.named_child(0).and_then(|n| n.utf8_text(source).ok()) {
                                        items.push((format!("{}.{}", name, var_name), FeatureType::Component));
                                    }
                                }
                                vc = v.next_named_sibling();
                            }
                        }
                        child = c.next_named_sibling();
                    }
                }
                return;
            }
            "impl_item" => {
                // Get the struct/enum name (first type_identifier child)
                let impl_name = node.named_child(0)
                    .filter(|c| c.kind() == "type_identifier")
                    .and_then(|n| n.utf8_text(source).ok())
                    .map(String::from);

                if let Some(name) = impl_name {
                    // Walk declaration_list for methods
                    let mut child = node.named_child(0);
                    while let Some(c) = child {
                        self.walk_node(c, source, items, Some(&name));
                        child = c.next_named_sibling();
                    }
                }
                return;
            }
            "trait_item" => {
                if let Some(name) = self.get_type_name(node, source) {
                    items.push((name.clone(), FeatureType::Component));
                    // Walk children for method signatures
                    let mut child = node.named_child(0);
                    while let Some(c) = child {
                        self.walk_node(c, source, items, Some(&name));
                        child = c.next_named_sibling();
                    }
                }
                return;
            }
            "function_signature_item" => {
                // Trait method signatures — extract name, nest under parent
                if let Some(name) = self.get_func_name_from_sig(node, source) {
                    if let Some(parent) = parent_name {
                        items.push((format!("{}.{}", parent, name), FeatureType::Logic));
                    }
                }
                return;
            }
            _ => {
                let mut child = node.named_child(0);
                while let Some(c) = child {
                    self.walk_node(c, source, items, parent_name);
                    child = c.next_named_sibling();
                }
            }
        }
    }

    /// Get struct/enum/trait name (first type_identifier child).
    fn get_type_name(&self, node: Node, source: &[u8]) -> Option<String> {
        node.named_child(0)
            .filter(|c| c.kind() == "type_identifier")
            .and_then(|n| n.utf8_text(source).ok())
            .map(String::from)
    }

    /// Get function name from function_item (first identifier child).
    fn get_func_name(&self, node: Node, source: &[u8]) -> Option<String> {
        node.named_child(0)
            .filter(|c| c.kind() == "identifier")
            .and_then(|n| n.utf8_text(source).ok())
            .map(String::from)
    }

    /// Get function name from function_signature_item.
    fn get_func_name_from_sig(&self, node: Node, source: &[u8]) -> Option<String> {
        node.named_child(0)
            .filter(|c| c.kind() == "identifier")
            .and_then(|n| n.utf8_text(source).ok())
            .map(String::from)
    }

    /// Cyclomatic complexity: base 1 + branches.
    fn count_complexity(&self, node: Node, source: &[u8]) -> u32 {
        let mut score: u32 = 1;
        let mut stack = vec![node];
        while let Some(current) = stack.pop() {
            match current.kind() {
                "if_expression" | "for_expression"
                | "while_expression" | "loop_expression"
                | "match_expression" => {
                    score += 1;
                }
                "match_arm" => {
                    score += 1;
                }
                "binary_expression" => {
                    // Check operator token
                    if let Some(op_node) = current.named_child(1) {
                        if let Ok(op) = op_node.utf8_text(source) {
                            if op == "&&" || op == "||" {
                                score += 1;
                            }
                        }
                    }
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

    /// Extract import edges from `use` items.
    fn extract_edges(&self, node: Node, source: &[u8]) -> Vec<Edge> {
        let mut edges = Vec::new();
        self.collect_edges(node, source, &mut edges);
        edges
    }

    fn collect_edges(&self, node: Node, source: &[u8], edges: &mut Vec<Edge>) {
        if node.kind() == "use_declaration" {
            self.parse_use_decl(node, source, edges);
        }
        let mut child = node.named_child(0);
        while let Some(c) = child {
            self.collect_edges(c, source, edges);
            child = c.next_named_sibling();
        }
    }

    fn parse_use_decl(&self, node: Node, source: &[u8], edges: &mut Vec<Edge>) {
        let first_child = match node.named_child(0) {
            Some(c) => c,
            None => return,
        };

        match first_child.kind() {
            "scoped_identifier" => {
                self.parse_scoped_identifier(first_child, source, edges);
            }
            "scoped_use_list" => {
                // e.g. serde::{Serialize, Deserialize}
                let source_name = first_child.named_child(0)
                    .and_then(|n| n.utf8_text(source).ok())
                    .map(String::from)
                    .unwrap_or_default();

                // Find the use_list child
                let mut child = first_child.named_child(0);
                while let Some(c) = child {
                    if c.kind() == "use_list" {
                        let mut ic = c.named_child(0);
                        while let Some(i) = ic {
                            if i.kind() == "identifier" {
                                if let Ok(name) = i.utf8_text(source) {
                                    edges.push(Edge {
                                        edge_type: "import".to_string(),
                                        name: name.to_string(),
                                        source: source_name.clone(),
                                    });
                                }
                            } else if i.kind() == "scoped_identifier" {
                                self.parse_scoped_identifier(i, source, edges);
                            }
                            ic = i.next_named_sibling();
                        }
                    }
                    child = c.next_named_sibling();
                }
            }
            _ => {}
        }
    }

    /// Parse scoped_identifier: std::collections::HashMap → source=collections, name=HashMap
    fn parse_scoped_identifier(&self, node: Node, source: &[u8], edges: &mut Vec<Edge>) {
        // Last child is the name, parent scope is the source
        let name = node.named_child(node.named_child_count() - 1)
            .and_then(|n| n.utf8_text(source).ok())
            .map(String::from);

        let scope = node.named_child(node.named_child_count() - 2)
            .and_then(|n| n.utf8_text(source).ok())
            .map(String::from);

        if let (Some(name), Some(source_path)) = (name, scope) {
            edges.push(Edge {
                edge_type: "import".to_string(),
                name,
                source: source_path,
            });
        }
    }
}

impl Analyzer for RustAnalyzer {
    fn languages(&self) -> &[&str] {
        &[".rs"]
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
            let complexity = self.count_complexity(root, &source);
            let edges = self.extract_edges(root, &source);

            if items.is_empty() && edges.is_empty() {
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
                edges: if edges.is_empty() { None } else { Some(edges) },
            });
        }

        Ok(results)
    }
}
