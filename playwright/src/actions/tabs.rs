use anyhow::Result;
use playwright::BrowserContext;
use crate::actions::CliArgs;

pub async fn action_tabs_open(context: &BrowserContext, args: &CliArgs) -> Result<()> {
    let count: usize = args.value.as_deref().unwrap_or("3").parse()?;
    for _ in 0..count {
        context.new_page().await?;
    }
    println!("{{\"count\": {}}}", context.pages().await.len());
    Ok(())
}

pub async fn action_tabs_list(context: &BrowserContext, _args: &CliArgs) -> Result<()> {
    let pages = context.pages().await;
    let result: Vec<serde_json::Value> = pages.iter().enumerate().map(|(i, p)| {
        serde_json::json!({ "index": i, "url": p.url(), "title": p.title().await })
    }).collect();
    println!("{}", serde_json::to_string_pretty(&result)?);
    Ok(())
}

pub async fn action_tabs_switch(context: &BrowserContext, args: &CliArgs) -> Result<()> {
    let index: usize = args.value.as_deref().ok_or_else(|| anyhow::anyhow!("No index"))?.parse()?;
    let pages = context.pages().await;
    if index >= pages.len() {
        anyhow::bail!("Tab index {} out of range (0–{})", index, pages.len() - 1);
    }
    let p = &pages[index];
    println!("{{\"url\": \"{}\", \"title\": \"{}\", \"index\": {}}}", p.url(), p.title().await, index);
    Ok(())
}

pub async fn action_tabs_close(context: &BrowserContext, args: &CliArgs) -> Result<()> {
    let index: usize = args.value.as_deref().ok_or_else(|| anyhow::anyhow!("No index"))?.parse()?;
    let pages = context.pages().await;
    if index < pages.len() {
        pages[index].close().await?;
    }
    println!("[tabs] Closed tab {index}");
    Ok(())
}

pub async fn action_tabs_close_all(context: &BrowserContext, _args: &CliArgs) -> Result<()> {
    for p in context.pages().await {
        p.close().await.ok();
    }
    println!("[tabs] Closed all tabs");
    Ok(())
}

pub async fn action_tabs_broadcast(context: &BrowserContext, args: &CliArgs) -> Result<()> {
    let specs: Vec<serde_json::Value> = serde_json::from_str(
        args.value.as_deref().ok_or_else(|| anyhow::anyhow!("No specs JSON"))?
    )?;
    let pages = context.pages().await;
    if specs.len() != pages.len() {
        anyhow::bail!("broadcast: {} specs for {} tabs", specs.len(), pages.len());
    }
    let mut results = Vec::new();
    for (p, spec) in pages.iter().zip(specs.iter()) {
        let action = spec["action"].as_str().ok_or_else(|| anyhow::anyhow!("Missing action"))?;
        let action_args = &spec["args"];
        match action {
            "goto" => {
                let url = action_args[0].as_str().ok_or_else(|| anyhow::anyhow!("No URL"))?;
                p.goto(url).wait_until(playwright::types::WaitUntil::DomContentLoaded).await?;
                results.push(serde_json::json!({ "url": p.url() }));
            }
            "evaluate" => {
                let expr = action_args[0].as_str().ok_or_else(|| anyhow::anyhow!("No expression"))?;
                let val: serde_json::Value = p.evaluate(expr).await?;
                results.push(val);
            }
            _ => {
                results.push(serde_json::json!({ "error": format!("Unsupported action: {}", action) }));
            }
        }
    }
    println!("{}", serde_json::to_string_pretty(&results)?);
    Ok(())
}

pub async fn action_tabs_gather(context: &BrowserContext, args: &CliArgs) -> Result<()> {
    let expr = args.value.as_deref().ok_or_else(|| anyhow::anyhow!("No expression"))?;
    let pages = context.pages().await;
    let mut results = Vec::new();
    for p in &pages {
        let val: serde_json::Value = p.evaluate(expr).await?;
        results.push(val);
    }
    println!("{}", serde_json::to_string_pretty(&results)?);
    Ok(())
}
