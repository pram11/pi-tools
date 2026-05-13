use anyhow::Result;
use playwright::api::page::Page;
use std::path::PathBuf;
use crate::actions::CliArgs;

pub async fn action_network(page: &Page, args: &CliArgs) -> Result<()> {
    let url = args.url.clone().ok_or_else(|| anyhow::anyhow!("No URL"))?;
    page.goto_builder(&url)
        .timeout(30000.0)
        .goto().await?;

    let result: serde_json::Value = page.eval("() => ({ url: location.href, title: document.title })").await?;
    println!("{}", serde_json::to_string_pretty(&result)?);
    Ok(())
}

pub async fn action_pdf(page: &Page, args: &CliArgs) -> Result<()> {
    let out = args.output.as_deref().unwrap_or("output.pdf");
    let path = if out.ends_with(".pdf") { out.to_string() } else { format!("{out}.pdf") };
    page.pdf_builder()
        .path(PathBuf::from(&path))
        .pdf().await?;
    println!("[pdf] Generated: {path}");
    Ok(())
}
