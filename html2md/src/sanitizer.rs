use ammonia::Builder;

/// Strip script/style/noscript tags and their content.
///
/// Uses [ammonia](https://crates.io/crates/ammonia) for general HTML sanitization,
/// with extra pass to remove script/style/noscript entirely (tag + content).
///
/// # Example
///
/// ```
/// use html2md::sanitizer::sanitize;
///
/// let out = sanitize("<p>hello</p><script>alert(1)</script>");
/// assert!(!out.contains("script"));
/// assert!(!out.contains("alert"));
/// assert!(out.contains("hello"));
/// ```
pub fn sanitize(html: &str) -> String {
    let mut builder = Builder::new();
    // Strip content from script/style/noscript (they're in default whitelist)
    builder.clean_content_tags(["script", "style", "noscript"].iter().cloned().collect());
    // Then remove the (now empty) tags so they're dropped during sanitization
    builder.rm_tags(["script", "style", "noscript"]);
    builder.clean(html).to_string()
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn doc_example() {
        let out = sanitize("<p>hello</p><script>alert(1)</script>");
        assert!(!out.contains("script"));
        assert!(!out.contains("alert"));
        assert!(out.contains("hello"));
    }
}
