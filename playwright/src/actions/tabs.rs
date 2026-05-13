use anyhow::Result;
use playwright::api::browser_context::BrowserContext;
use crate::actions::CliArgs;

pub async fn action_tabs_open(context: &BrowserContext, args: &CliArgs) -> Result<()> {
    let url = args.url.as_deref().ok_or_else(|| anyhow::anyhow!("No URL"))?;
    let page = context.new_page().await?;
    page.goto_builder(url).timeout(args.timeout as f64).goto().await?;
    let pages = context.pages()?;
    println!("{{\"page_index\": {}, \"total\": {}, \"url\": \"{}\"}}",
        pages.len() - 1, pages.len(), page.url()?);
    Ok(())
}

pub async fn action_tabs_list(context: &BrowserContext, _args: &CliArgs) -> Result<()> {
    let pages = context.pages()?;
    let tabs: Vec<serde_json::Value> = pages.iter().enumerate().map(|(i, p)| {
        serde_json::json!({
            "index": i,
            "url": p.url().unwrap_or_default(),
            "title": "",
        })
    }).collect();
    println!("{}", serde_json::to_string_pretty(&tabs)?);
    Ok(())
}

pub async fn action_tabs_switch(context: &BrowserContext, args: &CliArgs) -> Result<()> {
    let idx: usize = args.value.as_deref().unwrap_or("0").parse()?;
    let pages = context.pages()?;
    if idx >= pages.len() {
        anyhow::bail!("Page index {} out of range (total: {})", idx, pages.len());
    }
    println!("{{\"switched\": true, \"url\": \"{}\"}}", pages[idx].url()?);
    Ok(())
}

pub async fn action_tabs_close(context: &BrowserContext, args: &CliArgs) -> Result<()> {
    let idx: usize = args.value.as_deref().unwrap_or("0").parse()?;
    let pages = context.pages()?;
    if idx >= pages.len() {
        anyhow::bail!("Page index {} out of range", idx);
    }
    let page = &pages[idx];
    page.close(None).await.ok();
    let remaining = context.pages()?;
    println!("{{\"closed\": {}, \"remaining\": {}}}", idx, remaining.len());
    Ok(())
}

pub async fn action_tabs_close_all(context: &BrowserContext, _args: &CliArgs) -> Result<()> {
    let pages = context.pages()?;
    for p in pages {
        p.close(None).await.ok();
    }
    println!("{{\"closed\": true}}");
    Ok(())
}

pub async fn action_tabs_broadcast(context: &BrowserContext, args: &CliArgs) -> Result<()> {
    let _action = args.selector.as_deref().ok_or_else(|| anyhow::anyhow!("No action"))?;
    let pages = context.pages()?;
    let mut results = Vec::new();
    for p in &pages {
        let js = format!(r#"(sel) => {{ return document.querySelector(sel) ? true : false; }}"#);
        let r: bool = p.eval::<bool>(&js).await.unwrap_or(false);
        results.push(serde_json::json!({
            "url": p.url().unwrap_or_default(),
            "success": r,
        }));
    }
    println!("{}", serde_json::to_string_pretty(&results)?);
    Ok(())
}

pub async fn action_tabs_gather(context: &BrowserContext, args: &CliArgs) -> Result<()> {
    let sel = args.selector.as_deref().ok_or_else(|| anyhow::anyhow!("No selector"))?;
    let pages = context.pages()?;
    let mut gathered = Vec::new();
    for p in &pages {
        let js = format!(r#"
            (() => {{
                const els = document.querySelectorAll({});
                return Array.from(els).map(e => e.textContent.trim());
            }})()
        "#, serde_json::to_string(sel)?);
        let result: serde_json::Value = p.eval(&js).await.unwrap_or_default();
        gathered.push(serde_json::json!({
            "url": p.url().unwrap_or_default(),
            "data": result,
        }));
    }
    println!("{}", serde_json::to_string_pretty(&gathered)?);
    Ok(())
}
