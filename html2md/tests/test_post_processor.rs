use html2md::post_processor::process;

#[test]
fn strips_trailing_spaces() {
    let out = process("hello   \nworld   \n");
    assert!(!out.contains(" ")); // no trailing spaces
}

#[test]
fn collapses_triple_blanks() {
    let in_ = "line1\n\n\n\n\nline2";
    let out = process(in_);
    assert!(!out.contains("\n\n\n"), "no triple blanks");
    assert_eq!(out, "line1\n\nline2");
}

#[test]
fn trims_edges() {
    let out = process("\n\n  hello  \n\n");
    assert_eq!(out, "hello");
}

#[test]
fn empty_input() {
    assert_eq!(process(""), "");
}

#[test]
fn preserves_single_blanks() {
    let in_ = "line1\n\nline2";
    let out = process(in_);
    assert_eq!(out, "line1\n\nline2");
}

#[test]
fn preserves_headings() {
    let in_ = "\n\n# Heading\n\n";
    let out = process(in_);
    assert!(out.contains("# Heading"));
}

#[test]
fn preserves_list_markers() {
    let in_ = "- item1\n- item2";
    let out = process(in_);
    assert_eq!(out, "- item1\n- item2");
}
