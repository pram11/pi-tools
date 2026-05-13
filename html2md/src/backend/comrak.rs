use ego_tree::NodeRef;
use scraper::{ElementRef, Html, Node};

use crate::converter::{Converter, Result};
use crate::sanitizer;

/// Primary backend — full Markdown output via scraper DOM walk.
#[derive(Debug)]
pub struct ComrakBackend;

impl Converter for ComrakBackend {
    fn name(&self) -> &str {
        "comrak"
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
        "h1" | "h2" | "h3" | "h4" | "h5" | "h6" => {
            let level = (name.as_bytes()[1] - b'0').max(1) as usize;
            let prefix = "#".repeat(level);
            let t = text(el);
            buf.push_str(&format!("\n\n{} {}\n", prefix, t));
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
            buf.push_str(&format!("[{}]({})", t, href));
        }
        "strong" | "b" => {
            let t = el.text().collect::<Vec<_>>().join("");
            buf.push_str(&format!("**{}**", t));
        }
        "em" | "i" => {
            let t = el.text().collect::<Vec<_>>().join("");
            buf.push_str(&format!("*{}*", t));
        }
        "ul" => {
            for li in el.select(&scraper::Selector::parse("li").unwrap()) {
                buf.push_str(&format!("\n- {}", text(&li)));
            }
        }
        "ol" => {
            for (idx, li) in (1..).zip(el.select(&scraper::Selector::parse("li").unwrap())) {
                buf.push_str(&format!("\n{}. {}", idx, text(&li)));
            }
        }
        "code" => {
            if el
                .parent()
                .is_some_and(|p| ElementRef::wrap(p).is_some_and(|e| e.value().name() == "pre"))
            {
                let t = el.text().collect::<Vec<_>>().join("");
                buf.push_str(&format!("\n```\n{}\n```\n", t.trim()));
            } else {
                let t = el.text().collect::<Vec<_>>().join("");
                buf.push_str(&format!("`{}`", t));
            }
        }
        "pre" => {}
        "blockquote" => {
            let raw: String = el.text().collect::<Vec<_>>().join("\n");
            for line in raw.lines() {
                let t = line.trim();
                if !t.is_empty() {
                    buf.push_str(&format!("\n> {}", t));
                }
            }
        }
        "hr" => {
            buf.push_str("\n\n---\n");
        }
        "img" => {
            let alt = el.value().attr("alt").unwrap_or("");
            let src = el.value().attr("src").unwrap_or("");
            buf.push_str(&format!("[{}]({})", alt, src));
        }
        "table" => {
            let md = render_table(el);
            buf.push_str(&format!("\n\n{}", md));
        }
        _ => {
            for child in el.children() {
                walk_node(&child, buf);
            }
        }
    }
}

fn render_table(el: &ElementRef) -> String {
    let mut rows: Vec<Vec<String>> = Vec::new();
    for tr in el.select(&scraper::Selector::parse("tr").unwrap()) {
        let mut row = Vec::new();
        for cell in tr.select(&scraper::Selector::parse("td, th").unwrap()) {
            row.push(text(&cell));
        }
        if !row.is_empty() {
            rows.push(row);
        }
    }
    if rows.is_empty() {
        return String::new();
    }
    let cols = rows.first().map_or(0, |r| r.len());
    let mut md = String::new();
    md.push_str(&format!("| {} |\n", rows[0].join(" | ")));
    md.push_str(&format!(
        "| {} |\n",
        (0..cols).map(|_| "---").collect::<Vec<_>>().join(" | ")
    ));
    for row in &rows[1..] {
        let padded: Vec<String> = row
            .iter()
            .chain(std::iter::repeat(&String::new()))
            .take(cols)
            .cloned()
            .collect();
        md.push_str(&format!("| {} |\n", padded.join(" | ")));
    }
    md
}
