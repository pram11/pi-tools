use anyhow::Result;
use playwright::api::page::Page;
use crate::actions::CliArgs;
use crate::utils::retry;

pub async fn action_navigate(page: &Page, args: &CliArgs) -> Result<()> {
    let url = args.url.as_deref().ok_or_else(|| anyhow::anyhow!("No URL provided"))?;
    page.goto_builder(url).goto().await?;
    let current: serde_json::Value = page.eval("window.location.href").await?;
    println!("[navigate] Loaded: {}", current.as_str().unwrap_or(""));
    Ok(())
}
