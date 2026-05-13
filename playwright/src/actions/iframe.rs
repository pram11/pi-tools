use anyhow::Result;
use playwright::Page;
use crate::actions::CliArgs;

pub async fn action_iframe_list(page: &Page, _args: &CliArgs) -> Result<()> {
    let js = r#"() => {
        const frames = document.querySelectorAll('iframe');
        return Array.from(frames).map(f => ({
            name: f.id || f.name || '', src: f.src || 'inline',
            visible: f.offsetParent !== null
        }));
    }"#;
    let result: serde_json::Value = page.evaluate(js).await?;
    println!("{}", serde_json::to_string_pretty(&result)?);
    Ok(())
}

pub async fn action_iframe_query(page: &Page, args: &CliArgs) -> Result<()> {
    let iframe_sel = args.selector.as_deref().ok_or_else(|| anyhow::anyhow!("No iframe selector"))?;
    let inner = args.value.as_deref().ok_or_else(|| anyhow::anyhow!("No inner selector"))?;
    let frame = page.frame_locator(iframe_sel);
    let text = frame.locator(inner).inner_text().await;
    match text {
        Ok(t) if !t.is_empty() => println!("{t}"),
        _ => {}
    }
    Ok(())
}

pub async fn action_iframe_click(page: &Page, args: &CliArgs) -> Result<()> {
    let iframe_sel = args.selector.as_deref().ok_or_else(|| anyhow::anyhow!("No iframe selector"))?;
    let inner = args.value.as_deref().ok_or_else(|| anyhow::anyhow!("No inner selector"))?;
    page.frame_locator(iframe_sel).locator(inner).click().await?;
    println!("[iframe] Clicked: {iframe_sel} → {inner}");
    Ok(())
}

pub async fn action_iframe_fill(page: &Page, args: &CliArgs) -> Result<()> {
    let iframe_sel = args.selector.as_deref().ok_or_else(|| anyhow::anyhow!("No iframe selector"))?;
    let inner = args.value.as_deref().ok_or_else(|| anyhow::anyhow!("No inner selector"))?;
    let text = args.output.as_deref().unwrap_or("");
    page.frame_locator(iframe_sel).locator(inner).fill(text).await?;
    println!("[iframe] Filled: {iframe_sel} → {inner}");
    Ok(())
}

pub async fn action_iframe_extract(page: &Page, args: &CliArgs) -> Result<()> {
    let iframe_sel = args.selector.as_deref().ok_or_else(|| anyhow::anyhow!("No iframe selector"))?;
    let inner = args.value.as_deref().ok_or_else(|| anyhow::anyhow!("No inner selector"))?;
    let text = page.frame_locator(iframe_sel).locator(inner).inner_text().await.unwrap_or_default();
    println!("{text}");
    Ok(())
}
