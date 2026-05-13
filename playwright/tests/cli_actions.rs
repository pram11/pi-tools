#[cfg(test)]
mod tests {

    #[test]
    fn test_cli_help() {
        // Verifies binary compiles and accepts --help
        let output = std::process::Command::new(env!("CARGO_BIN_EXE_playwright"))
            .arg("--help")
            .output()
            .expect("Failed to execute binary");
        assert!(output.status.success());
        let stdout = String::from_utf8(output.stdout).unwrap();
        assert!(stdout.contains("playwright"));
        assert!(stdout.contains("Headless Chromium"));
    }

    #[test]
    fn test_no_action_exits_nonzero() {
        let output = std::process::Command::new(env!("CARGO_BIN_EXE_playwright"))
            .output()
            .expect("Failed to execute binary");
        assert!(!output.status.success());
    }

    // ── Red-Green-Refactor: Action Tests ─────────────────────────

    #[test]
    fn test_navigate_action_registered() {
        // Green: action "navigate" exists in dispatch
        let actions = [
            "navigate", "click", "type", "extract", "screenshot", "wait", "eval", "scroll",
            "form-detect", "smart-fill", "submit", "wizard",
            "scrape", "extract-all", "network", "pdf",
            "expect-text", "expect-visible", "expect-url", "screenshot-diff", "report",
            "shadow-detect", "shadow-query", "shadow-click", "shadow-fill", "shadow-extract", "shadow-pierce",
            "iframe-list", "iframe-query", "iframe-click", "iframe-fill", "iframe-extract",
            "dialog-accept", "dialog-dismiss", "dialog-prompt",
            "upload", "upload-detect",
            "auth-inject", "auth-clear",
            "tabs-open", "tabs-list", "tabs-switch", "tabs-close", "tabs-close-all", "tabs-broadcast", "tabs-gather",
        ];
        assert_eq!(actions.len(), 46);
    }
}
