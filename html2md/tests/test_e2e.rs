use std::process::Command;

const BIN: &str = env!("CARGO_BIN_EXE_html2md");

fn run(args: &[&str]) -> std::process::Output {
    Command::new(BIN).args(args).output().unwrap()
}

fn run_with_input(input: &str, args: &[&str]) -> std::process::Output {
    let mut child = Command::new(BIN)
        .args(args)
        .stdin(std::process::Stdio::piped())
        .stdout(std::process::Stdio::piped())
        .stderr(std::process::Stdio::piped())
        .spawn()
        .unwrap();
    use std::io::Write;
    child
        .stdin
        .take()
        .unwrap()
        .write_all(input.as_bytes())
        .unwrap();
    child.wait_with_output().unwrap()
}

fn stdout(out: &std::process::Output) -> String {
    String::from_utf8_lossy(&out.stdout).to_string()
}

fn stderr(out: &std::process::Output) -> String {
    String::from_utf8_lossy(&out.stderr).to_string()
}

#[test]
fn no_args_exits_1() {
    let out = run(&[]);
    assert_eq!(out.status.code(), Some(1));
}

#[test]
fn html_flag_heading() {
    let out = run(&["--html", "<h1>Hello</h1>"]);
    assert_eq!(out.status.code(), Some(0));
    assert!(stdout(&out).contains("Hello"));
}

#[test]
fn html_flag_paragraph() {
    let out = run(&["--html", "<p>World</p>"]);
    assert!(stdout(&out).contains("World"));
}

#[test]
fn file_flag() {
    let tmp = tempfile::NamedTempFile::new().unwrap();
    std::fs::write(tmp.path(), "<h2>FromFile</h2>").unwrap();
    let out = run(&["--file", tmp.path().to_str().unwrap()]);
    assert_eq!(out.status.code(), Some(0));
    assert!(stdout(&out).contains("FromFile"));
}

#[test]
fn file_not_found() {
    let out = run(&["--file", "/nonexistent/path.html"]);
    assert_eq!(out.status.code(), Some(1));
    assert!(stderr(&out).contains("not found"));
}

#[test]
fn backend_flag_custom() {
    let out = run(&["--html", "<h1>X</h1>", "--backend", "custom"]);
    assert_eq!(out.status.code(), Some(0));
    assert!(stdout(&out).contains("X"));
}

#[test]
fn backend_unknown() {
    let out = run(&["--html", "<p>x</p>", "--backend", "bad"]);
    assert_eq!(out.status.code(), Some(1));
}

#[test]
fn output_flag() {
    let out_path = tempfile::NamedTempFile::new().unwrap();
    let out_path = out_path.path();
    let out = run(&[
        "--html",
        "<p>out</p>",
        "--output",
        out_path.to_str().unwrap(),
    ]);
    assert_eq!(out.status.code(), Some(0));
    let content = std::fs::read_to_string(out_path).unwrap();
    assert!(content.contains("out"));
}

#[test]
fn stdin_pipe() {
    let out = run_with_input("<h1>Stdin</h1>", &[]);
    assert_eq!(out.status.code(), Some(0));
    assert!(stdout(&out).contains("Stdin"));
}

#[test]
fn wrap_flag() {
    let html = "<p>This is a very long line that should be wrapped at a certain width</p>";
    let out = run(&["--html", html, "--wrap", "20"]);
    let md = stdout(&out);
    for line in md.lines() {
        assert!(line.len() <= 20, "line too long: {:?}", line);
    }
}

#[test]
fn strip_images() {
    let html = r#"<p><img src="x.jpg" alt="photo"> text</p>"#;
    let out = run(&["--html", html, "--strip-images"]);
    let md = stdout(&out);
    assert!(!md.contains("img"));
    assert!(!md.contains("photo"));
}

#[test]
fn strip_links() {
    let html = r#"<p><a href="https://example.com">link</a></p>"#;
    let out = run(&["--html", html, "--strip-links"]);
    let md = stdout(&out);
    assert!(md.contains("link"));
    assert!(!md.contains("example.com"));
}

#[test]
fn sanitize_script() {
    let html = "<p>safe</p><script>alert(1)</script>";
    let out = run(&["--html", html]);
    let md = stdout(&out);
    assert!(md.contains("safe"));
    assert!(!md.contains("alert"));
}
