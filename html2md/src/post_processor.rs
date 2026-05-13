/// Clean Markdown output: strip trailing spaces, collapse 3+ blanks → 1, trim edges.
///
/// # Example
///
/// ```
/// use html2md::post_processor::process;
///
/// let out = process("hello\n\n\n\n\nworld");
/// assert_eq!(out, "hello\n\nworld");
/// ```
pub fn process(md: &str) -> String {
    // Strip trailing whitespace from each line
    let lines: Vec<String> = md.lines().map(|l| l.trim_end().to_string()).collect();
    // Collapse 3+ consecutive newlines → 1
    let mut joined = lines.join("\n");
    let result = loop {
        let collapsed = joined.replace("\n\n\n", "\n\n");
        if collapsed == joined {
            break collapsed;
        }
        joined = collapsed;
    };
    result.trim().to_string()
}
