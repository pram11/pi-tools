use html2md::sanitizer::sanitize;

#[test]
fn strips_script_tags() {
    let html = r#"<p>hello</p><script>alert('xss')</script><p>world</p>"#;
    let out = sanitize(html);
    assert!(!out.contains("script"), "script tag should be removed");
    assert!(!out.contains("alert"), "script content should be removed");
    assert!(out.contains("hello"), "valid content preserved");
    assert!(out.contains("world"), "valid content preserved");
}

#[test]
fn strips_style_tags() {
    let html = r#"<h1>Title</h1><style>body{color:red}</style>"#;
    let out = sanitize(html);
    assert!(!out.contains("style"), "style tag should be removed");
    assert!(!out.contains("color"), "style content should be removed");
    assert!(out.contains("Title"), "valid content preserved");
}

#[test]
fn strips_noscript_tags() {
    let html = r#"<p>text</p><noscript>No JS</noscript>"#;
    let out = sanitize(html);
    assert!(!out.contains("noscript"), "noscript tag should be removed");
    assert!(!out.contains("No JS"), "noscript content should be removed");
    assert!(out.contains("text"), "valid content preserved");
}

#[test]
fn preserves_valid_html() {
    let html = "<h1>Heading</h1><p>Para with <a href=\"#\">link</a></p>";
    let out = sanitize(html);
    assert!(out.contains("Heading"));
    assert!(out.contains("Para"));
    assert!(out.contains("link"));
}

#[test]
fn preserves_img_tags() {
    let html = r#"<p><img src="photo.jpg" alt="photo"></p>"#;
    let out = sanitize(html);
    assert!(out.contains("img"));
    assert!(out.contains("photo"));
}

#[test]
fn empty_input() {
    assert_eq!(sanitize(""), "");
}

#[test]
fn nested_script_in_valid_content() {
    let html = r#"<div><p>safe</p><script>bad()</script></div>"#;
    let out = sanitize(html);
    assert!(!out.contains("script"));
    assert!(!out.contains("bad()"));
    assert!(out.contains("safe"));
}
