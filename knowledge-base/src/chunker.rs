use std::collections::HashSet;
use std::path::Path;
use tree_sitter::{Parser, Node};

pub const MAX_CHUNK_SIZE: usize = 4096;

pub struct Chunk {
    pub index: usize,
    pub content: String,
    pub kind: String,
    pub start_byte: usize,
}

fn lang_key(ext: &str) -> Option<tree_sitter::Language> {
    match ext {
        ".py" => Some(tree_sitter::Language::from(tree_sitter_python::LANGUAGE)),
        ".js" | ".jsx" => Some(tree_sitter::Language::from(tree_sitter_javascript::LANGUAGE)),
        ".ts" => Some(tree_sitter::Language::from(tree_sitter_typescript::LANGUAGE_TYPESCRIPT)),
        ".tsx" => Some(tree_sitter::Language::from(tree_sitter_typescript::LANGUAGE_TSX)),
        ".java" => Some(tree_sitter::Language::from(tree_sitter_java::LANGUAGE)),
        ".c" | ".h" => Some(tree_sitter::Language::from(tree_sitter_c::LANGUAGE)),
        ".cpp" | ".hpp" => Some(tree_sitter::Language::from(tree_sitter_cpp::LANGUAGE)),
        ".rs" => Some(tree_sitter::Language::from(tree_sitter_rust::LANGUAGE)),
        ".go" => Some(tree_sitter::Language::from(tree_sitter_go::LANGUAGE)),
        _ => None,
    }
}

fn target_types(ext: &str) -> HashSet<&'static str> {
    match ext {
        ".py" => ["function_definition", "class_definition"].into(),
        ".js" | ".jsx" => ["function_declaration", "class_declaration", "method_definition", "arrow_function"].into(),
        ".ts" => ["function_declaration", "class_declaration", "method_definition", "interface_declaration", "type_alias_declaration"].into(),
        ".tsx" => ["function_declaration", "class_declaration", "method_definition", "interface_declaration"].into(),
        ".rs" => ["function_item", "struct_item", "impl_item"].into(),
        ".go" => ["function_declaration"].into(),
        _ => ["function_definition", "class_definition"].into(),
    }
}

fn collect_defs(node: Node, targets: &HashSet<&'static str>, out: &mut Vec<(usize, usize, String)>) {
    if targets.contains(node.kind()) {
        out.push((node.start_byte(), node.end_byte(), node.kind().to_string()));
        return;
    }
    let mut cursor = node.walk();
    for child in node.children(&mut cursor) {
        collect_defs(child, targets, out);
    }
}

fn line_chunk(content: &str) -> Vec<Chunk> {
    let lines: Vec<&str> = content.lines().collect();
    let chunk_lines = (MAX_CHUNK_SIZE / 60).max(10);
    let mut chunks = Vec::new();
    for i in (0..lines.len()).step_by(chunk_lines) {
        let end = (i + chunk_lines).min(lines.len());
        let block = lines[i..end].join("\n").trim().to_string();
        if block.is_empty() {
            continue;
        }
        let first_line = block.lines().next().unwrap_or("");
        let start_byte = content.find(first_line).unwrap_or(0);
        chunks.push(Chunk {
            index: chunks.len(),
            content: block,
            kind: "text".into(),
            start_byte,
        });
    }
    chunks
}

pub fn chunk_file(file_path: &Path) -> Vec<Chunk> {
    let content = std::fs::read_to_string(file_path).unwrap_or_default();
    let ext = file_path.extension().and_then(|s| s.to_str()).unwrap_or("");
    let ext_with_dot = format!(".{}", ext);
    let source_bytes = content.as_bytes();
    let mut chunks = Vec::new();

    if let Some(lang) = lang_key(&ext_with_dot) {
        let mut parser = Parser::new();
        if parser.set_language(&lang).is_ok() {
            if let Some(tree) = parser.parse(&content, None) {
                let root = tree.root_node();
                let targets = target_types(&ext_with_dot);
                let mut defs = Vec::new();
                collect_defs(root, &targets, &mut defs);
                for (start, end, kind) in defs {
                    let text = std::str::from_utf8(&source_bytes[start..end]).unwrap_or("").trim().to_string();
                    if !text.is_empty() {
                        chunks.push(Chunk {
                            index: chunks.len(),
                            content: text,
                            kind,
                            start_byte: start,
                        });
                    }
                }
            }
        }
    }

    if chunks.is_empty() {
        chunks = line_chunk(&content);
    }

    chunks
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::io::Write;
    use tempfile::NamedTempFile;

    fn write_temp(content: &str, ext: &str) -> NamedTempFile {
        let mut f = NamedTempFile::with_suffix(ext).expect("create temp");
        f.write_all(content.as_bytes()).expect("write temp");
        f
    }

    #[test]
    fn test_chunk_python_functions_and_classes() {
        let f = write_temp(
            r#"def hello():
    print("hi")

class Foo:
    def bar(self):
        pass

def world(x):
    return x * 2
"#,
            ".py",
        );
        let chunks = chunk_file(f.path());
        assert!(!chunks.is_empty(), "should produce chunks");
        let kinds: Vec<_> = chunks.iter().map(|c| c.kind.as_str()).collect();
        assert!(kinds.contains(&"function_definition"), "expect function_definition");
        assert!(kinds.contains(&"class_definition"), "expect class_definition");
    }

    #[test]
    fn test_chunk_rust_functions_and_impl() {
        let f = write_temp(
            r#"fn hello() -> &'static str {
    "hi"
}

struct Foo {
    x: i32,
}

impl Foo {
    fn bar(&self) -> i32 {
        self.x
    }
}
"#,
            ".rs",
        );
        let chunks = chunk_file(f.path());
        assert!(!chunks.is_empty(), "should produce chunks");
        let kinds: Vec<_> = chunks.iter().map(|c| c.kind.as_str()).collect();
        assert!(kinds.contains(&"function_item"), "expect function_item");
        assert!(kinds.contains(&"struct_item"), "expect struct_item");
        assert!(kinds.contains(&"impl_item"), "expect impl_item");
    }

    #[test]
    fn test_chunk_go_functions() {
        let f = write_temp(
            r#"package main

func hello() {
    println("hi")
}

func add(a, b int) int {
    return a + b
}
"#,
            ".go",
        );
        let chunks = chunk_file(f.path());
        assert!(!chunks.is_empty(), "should produce chunks");
        let kinds: Vec<_> = chunks.iter().map(|c| c.kind.as_str()).collect();
        assert!(kinds.contains(&"function_declaration"), "expect function_declaration");
    }

    #[test]
    fn test_chunk_js_functions_and_classes() {
        let f = write_temp(
            r#"function hello() {
    console.log("hi");
}

class Foo {
    bar() {
        return 1;
    }
}

const arrow = () => 42;
"#,
            ".js",
        );
        let chunks = chunk_file(f.path());
        assert!(!chunks.is_empty(), "should produce chunks");
        let kinds: Vec<_> = chunks.iter().map(|c| c.kind.as_str()).collect();
        assert!(kinds.contains(&"function_declaration"), "expect function_declaration");
        assert!(kinds.contains(&"class_declaration"), "expect class_declaration");
        assert!(kinds.contains(&"arrow_function"), "expect arrow_function");
    }

    #[test]
    fn test_chunk_plaintext_fallback() {
        let f = write_temp("line1\nline2\nline3", ".txt");
        let chunks = chunk_file(f.path());
        assert!(!chunks.is_empty(), "plain text fallback should produce chunks");
        assert_eq!(chunks[0].kind, "text");
    }

    #[test]
    fn test_chunk_c_functions() {
        let f = write_temp(
            r#"#include <stdio.h>

int add(int a, int b) {
    return a + b;
}

void hello() {
    printf("hi");
}
"#,
            ".c",
        );
        let chunks = chunk_file(f.path());
        assert!(!chunks.is_empty(), "C file should produce chunks");
    }

    #[test]
    fn test_chunk_empty_file() {
        let f = write_temp("", ".py");
        let chunks = chunk_file(f.path());
        assert!(chunks.is_empty(), "empty file → no chunks");
    }

    #[test]
    fn test_chunk_indices_sequential() {
        let f = write_temp(
            r#"def a(): pass
def b(): pass
def c(): pass
"#,
            ".py",
        );
        let chunks = chunk_file(f.path());
        let indices: Vec<_> = chunks.iter().map(|c| c.index).collect();
        let expected: Vec<_> = (0..chunks.len()).collect();
        assert_eq!(indices, expected, "indices must be sequential");
    }
}
