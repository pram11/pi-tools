use anyhow::{Result, bail};
use playwright::Page;
use crate::actions::CliArgs;

pub async fn action_assert_text(page: &Page, args: &CliArgs) -> Result<()> {
    let sel = args.selector.as_deref().ok_or_else(|| anyhow::anyhow!("No selector"))?;
    let expected = args.value.as_deref().ok_or_else(|| anyhow::anyhow!("No expected value"))?;
    let text = page.inner_text(sel).await.unwrap_or_default();
    if !text.contains(expected) {
        bail!("expect-text failed on {sel}: expected '{expected}' in '{text}'");
    }
    println!("[assert] expect-text passed: {sel} contains '{expected}'");
    Ok(())
}

pub async fn action_assert_visible(page: &Page, args: &CliArgs) -> Result<()> {
    let sel = args.selector.as_deref().ok_or_else(|| anyhow::anyhow!("No selector"))?;
    page.wait_for_selector(sel).state(playwright::types::WaitForSelectorState::Visible)
        .timeout(5000).await?;
    println!("[assert] expect-visible passed: {sel}");
    Ok(())
}

pub async fn action_assert_url(page: &Page, args: &CliArgs) -> Result<()> {
    let expected = args.value.as_deref().ok_or_else(|| anyhow::anyhow!("No expected URL"))?;
    let actual = page.url().await;
    if !actual.contains(expected) {
        bail!("expect-url failed: expected '{expected}' in '{actual}'");
    }
    println!("[assert] expect-url passed: contains '{expected}'");
    Ok(())
}

pub async fn action_report(page: &Page, args: &CliArgs) -> Result<()> {
    let specs: Vec<serde_json::Value> = serde_json::from_str(
        args.value.as_deref().ok_or_else(|| anyhow::anyhow!("No specs JSON"))?
    )?;

    let mut results = Vec::new();
    for spec in &specs {
        let atype = spec["type"].as_str().ok_or_else(|| anyhow::anyhow!("Missing type"))?;
        let selector = spec.get("selector").and_then(|v| v.as_str()).unwrap_or("");
        let value = spec.get("value").and_then(|v| v.as_str()).unwrap_or("");

        let ok = match atype {
            "expect-text" => {
                let text = page.inner_text(selector).await.unwrap_or_default();
                text.contains(value)
            }
            "expect-visible" => {
                page.wait_for_selector(selector).state(playwright::types::WaitForSelectorState::Visible)
                    .timeout(5000).await.is_ok()
            }
            "expect-url" => {
                page.url().await.contains(value)
            }
            _ => {
                results.push(serde_json::json!({
                    "assertion": atype, "selector": selector, "value": value,
                    "status": "FAIL", "error": "Unknown assertion type"
                }));
                continue;
            }
        };

        results.push(serde_json::json!({
            "assertion": atype, "selector": selector, "value": value,
            "status": if ok { "PASS" } else { "FAIL" },
            "error": if ok { "" } else { "Assertion failed" }
        }));
    }

    let passed = results.iter().filter(|r| r["status"] == "PASS").count();
    let failed = results.iter().filter(|r| r["status"] == "FAIL").count();
    let output = serde_json::json!({
        "total": results.len(),
        "passed": passed,
        "failed": failed,
        "results": results,
    });
    println!("{}", serde_json::to_string_pretty(&output)?);
    Ok(())
}
