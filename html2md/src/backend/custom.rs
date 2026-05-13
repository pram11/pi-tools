use ego_tree::NodeRef;
use scraper::{ElementRef, Html, Node};

use crate::converter::{Converter, Result};
use crate::sanitizer;

/// Fallback backend — simplified output (like html2text).
#[derive(Debug)]
pub struct CustomBackend;

impl Converter for CustomBackend {
    fn name(&self) -> &str {
        "custom"
    }

    fn convert(&self, html: &str) -> Result<String> {
        let cleaned = sanitizer::sanitize(html);
        let fragment = Html::parse_fragment(&cleaned);
        let mut buf = String::new();
        for child in fragment.root_element().children() {
            walk_node(&child, &mut buf);
        }
        Ok(buf.trim_end().to_string())
    }
}

fn walk_node(node: &NodeRef<'_, Node>, buf: &mut String) {
    match node.value() {
        Node::Text(text) => {
            let t = text.trim();
            if !t.is_empty() {
                buf.push_str(t);
                buf.push(' ');
            }
        }
        Node::Element(_) => {
            if let Some(el) = ElementRef::wrap(*node) {
                walk_element(&el, buf);
            }
        }
        _ => {}
    }
}

fn text(el: &ElementRef) -> String {
    el.text().collect::<Vec<_>>().join(" ").trim().to_string()
}

fn walk_element(el: &ElementRef, buf: &mut String) {
    let name = el.value().name();
    match name {
        "h1" => {
            buf.push_str(&format!("\n\n## {}\n", text(el)));
        }
        "h2" | "h3" | "h4" | "h5" | "h6" => {
            buf.push_str(&format!("\n\n### {}\n", text(el)));
        }
        "p" => {
            let t = text(el);
            if !t.is_empty() {
                buf.push_str(&format!("\n\n{}\n", t));
            }
        }
        "br" => {
            buf.push('\n');
        }
        "a" => {
            let t = el.text().collect::<Vec<_>>().join("");
            let href = el.value().attr("href").unwrap_or("");
            buf.push_str(&format!("{} ({})", t, href));
        }
        "strong" | "b" => {
            let t = el.text().collect::<Vec<_>>().join("");
            buf.push_str(&format!("[{}]", t));
        }
        "ul" | "ol" => {
            for li in el.select(&scraper::Selector::parse("li").unwrap()) {
                buf.push_str(&format!("\n* {}", text(&li)));
            }
        }
        "code" => {
            let t = el.text().collect::<Vec<_>>().join("");
            buf.push_str(&format!("<{}>", t));
        }
        "blockquote" => {
            let raw: String = el.text().collect::<Vec<_>>().join("\n");
            for line in raw.lines() {
                let t = line.trim();
                if !t.is_empty() {
                    buf.push_str(&format!("\n    {}", t));
                }
            }
        }
        "hr" => {
            buf.push_str("\n\n---\n");
        }
        _ => {
            for child in el.children() {
                walk_node(&child, buf);
            }
        }
    }
}
