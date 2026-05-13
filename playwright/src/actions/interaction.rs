use anyhow::Result;
use playwright::api::page::Page;
use crate::actions::CliArgs;

pub async fn action_click(page: &Page, args: &CliArgs) -> Result<()> {
    let sel = args.selector.as_deref().ok_or_else(|| anyhow::anyhow!("No selector"))?;
    page.click_builder(sel).timeout(args.timeout as f64).click().await?;
    println!("[click] Clicked: {sel}");
    Ok(())
}

pub async fn action_type(page: &Page, args: &CliArgs) -> Result<()> {
    let sel = args.selector.as_deref().ok_or_else(|| anyhow::anyhow!("No selector"))?;
    let val = args.value.as_deref().ok_or_else(|| anyhow::anyhow!("No value"))?;
    page.fill_builder(sel, val).fill().await?;
    println!("[type] Filled {sel}: {}", &val[..val.len().min(40)]);
    Ok(())
}

pub async fn action_wait(page: &Page, args: &CliArgs) -> Result<()> {
    let sel = args.selector.as_deref().ok_or_else(|| anyhow::anyhow!("No selector"))?;
    let timeout: u64 = args.value.as_deref().unwrap_or("5000").parse()?;
    page.wait_for_selector_builder(sel)
        .timeout(timeout as f64)
        .wait_for_selector().await?;
    println!("[wait] Element found: {sel}");
    Ok(())
}

pub async fn action_eval(page: &Page, args: &CliArgs) -> Result<()> {
    let expr = args.value.as_deref().ok_or_else(|| anyhow::anyhow!("No expression"))?;
    let result: serde_json::Value = page.eval(expr).await?;
    println!("{}", serde_json::to_string_pretty(&result)?);
    Ok(())
}

pub async fn action_scroll(page: &Page, args: &CliArgs) -> Result<()> {
    let val = args.value.as_deref().unwrap_or("top");
    let js = match val {
        "top" => "window.scrollTo(0, 0)".to_string(),
        "bottom" => "window.scrollTo(0, document.body.scrollHeight)".to_string(),
        _ => format!("window.scrollTo(0, {})", val.parse::<i32>()?),
    };
    page.eval::<()>(&js).await?;
    println!("[scroll] Scrolled to: {val}");
    Ok(())
}
