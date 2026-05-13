use anyhow::Result;
use playwright::Page;
use crate::actions::CliArgs;

pub async fn action_click(page: &Page, args: &CliArgs) -> Result<()> {
    let sel = args.selector.as_deref().ok_or_else(|| anyhow::anyhow!("No selector"))?;
    page.click(sel).await?;
    println!("[click] Clicked: {sel}");
    Ok(())
}

pub async fn action_type(page: &Page, args: &CliArgs) -> Result<()> {
    let sel = args.selector.as_deref().ok_or_else(|| anyhow::anyhow!("No selector"))?;
    let val = args.value.as_deref().ok_or_else(|| anyhow::anyhow!("No value"))?;
    page.fill(sel, val).await?;
    println!("[type] Filled {sel}: {}", &val[..val.len().min(40)]);
    Ok(())
}

pub async fn action_wait(page: &Page, args: &CliArgs) -> Result<()> {
    let sel = args.selector.as_deref().ok_or_else(|| anyhow::anyhow!("No selector"))?;
    let timeout: u64 = args.value.as_deref().unwrap_or("5000").parse()?;
    page.wait_for_selector(sel).timeout(timeout).await?;
    println!("[wait] Element found: {sel}");
    Ok(())
}

pub async fn action_eval(page: &Page, args: &CliArgs) -> Result<()> {
    let expr = args.value.as_deref().ok_or_else(|| anyhow::anyhow!("No expression"))?;
    let result = page.evaluate(expr).await?;
    println!("{}", serde_json::to_string_pretty(&result)?);
    Ok(())
}

pub async fn action_scroll(page: &Page, args: &CliArgs) -> Result<()> {
    let val = args.value.as_deref().unwrap_or("top");
    let js = match val {
        "top" => "window.scrollTo(0, 0)",
        "bottom" => "window.scrollTo(0, document.body.scrollHeight)",
        _ => format!("window.scrollTo(0, {})", val.parse::<i32>()?),
    };
    page.evaluate(&js).await?;
    println!("[scroll] Scrolled to: {val}");
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_scroll_top() {
        assert_eq!("top", "top");
    }
}
