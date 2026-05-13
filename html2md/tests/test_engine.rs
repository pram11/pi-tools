use html2md::engine::{convert, get_backend};

#[test]
fn get_backend_comrak() {
    let b = get_backend("comrak").unwrap();
    assert_eq!(b.name(), "comrak");
}

#[test]
fn get_backend_custom() {
    let b = get_backend("custom").unwrap();
    assert_eq!(b.name(), "custom");
}

#[test]
fn get_backend_unknown_fails() {
    let err = get_backend("nonexistent").unwrap_err();
    assert!(err.to_string().contains("nonexistent"));
}

#[test]
fn convert_heading_comrak() {
    let md = convert("<h1>Hello</h1>", "comrak").unwrap();
    assert!(md.contains("# Hello"));
}

#[test]
fn convert_heading_custom() {
    let md = convert("<h1>Hello</h1>", "custom").unwrap();
    assert!(md.contains("Hello"));
}

#[test]
fn convert_paragraph() {
    let md = convert("<p>Test paragraph</p>", "comrak").unwrap();
    assert!(md.contains("Test paragraph"));
}

#[test]
fn convert_link() {
    let md = convert(r#"<a href="https://example.com">link</a>"#, "comrak").unwrap();
    assert!(md.contains("[link](https://example.com)"));
}

#[test]
fn convert_list() {
    let md = convert("<ul><li>A</li><li>B</li></ul>", "comrak").unwrap();
    assert!(md.contains("- A"));
    assert!(md.contains("- B"));
}

#[test]
fn convert_sanitizes_script() {
    let md = convert("<p>safe</p><script>bad()</script>", "comrak").unwrap();
    assert!(!md.contains("script"));
    assert!(!md.contains("bad()"));
}

#[test]
fn convert_unknown_backend() {
    let err = convert("<p>x</p>", "fake").unwrap_err();
    assert!(err.to_string().contains("fake"));
}
