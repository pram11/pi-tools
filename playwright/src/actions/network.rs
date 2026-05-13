use anyhow::Result;
use playwright::{BrowserContext, Page};
use crate::actions::CliArgs;

pub async fn action_network(page: &Page, _context: &BrowserContext, args: &CliArgs) -> Result<()> {
    let url = args.url.clone().ok_or_else(|| anyhow::anyhow!("No URL"))?;

    let mut captured: Vec<serde_json::Value> = Vec::new();
    let captured_clone = std::sync::Arc::new(std::sync::Mutex::new(&mut captured));

    page.goto(&url)
        .wait_until(playwright::types::WaitUntil::NetworkIdle)
        .timeout(30000)
        .await?;

    // Note: full network interception requires page.on("response") in async
    // This is a simplified version — captures page metadata
    let result: serde_json::Value = page.evaluate("() => ({ url: location.href, title: document.title })").await?;
    println!("{}", serde_json::to_string_pretty(&result)?);
    Ok(())
}

pub async fn action_pdf(page: &Page, args: &CliArgs) -> Result<()> {
    let out = args.output.as_deref().unwrap_or("output.pdf");
    let path = if out.ends_with(".pdf") { out.to_string() } else { format!("{out}.pdf") };
    page.pdf().path(&path).await?;
    println!("[pdf] Generated: {path}");
    Ok(())
}
