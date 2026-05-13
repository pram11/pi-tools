use anyhow::Result;
use playwright::api::page::Page;
use crate::actions::CliArgs;

fn js_get_frame(index: usize) -> String {
    format!("(() => {{ const iframes = document.querySelectorAll('iframe'); return iframes[{}] ? (iframes[{}].contentDocument || iframes[{}].contentWindow.document) : null; }})()", index, index, index)
}

fn js_get_frame_by_selector(sel: &str) -> String {
    let sel_json = serde_json::to_string(sel).unwrap_or_default();
    format!("(() => {{ const iframe = document.querySelector({}); return iframe ? (iframe.contentDocument || iframe.contentWindow.document) : null; }})()", sel_json)
}

pub async fn action_iframe_list(page: &Page, _args: &CliArgs) -> Result<()> {
    let js = r#"() => {
        const iframes = document.querySelectorAll('iframe');
        return Array.from(iframes).map((f, i) => ({
            index: i,
            src: f.src || f.getAttribute('src') || '',
            title: f.title || '',
            name: f.name || '',
        }));
    }"#;
    let result: serde_json::Value = page.eval(js).await?;
    println!("{}", serde_json::to_string_pretty(&result)?);
    Ok(())
}

pub async fn action_iframe_query(page: &Page, args: &CliArgs) -> Result<()> {
    let sel = args.selector.as_deref().ok_or_else(|| anyhow::anyhow!("No selector"))?;
    let val = args.value.as_deref().unwrap_or("*");
    let val_json = serde_json::to_string(val)?;

    let js = if let Ok(idx) = sel.parse::<usize>() {
        format!("(() => {{ const f = ({}); return f ? Array.from(f.querySelectorAll({})).map(e => e.textContent.trim()) : []; }})()", js_get_frame(idx), val_json)
    } else {
        format!("(() => {{ const f = ({})(); return f ? Array.from(f.querySelectorAll({})).map(e => e.textContent.trim()) : []; }})()", js_get_frame_by_selector(sel), val_json)
    };

    let result: serde_json::Value = page.eval(&js).await?;
    println!("{}", serde_json::to_string_pretty(&result)?);
    Ok(())
}

pub async fn action_iframe_click(page: &Page, args: &CliArgs) -> Result<()> {
    let iframe_sel = args.selector.as_deref().ok_or_else(|| anyhow::anyhow!("No selector"))?;
    let child_sel = args.value.as_deref().ok_or_else(|| anyhow::anyhow!("No child selector"))?;
    let child_json = serde_json::to_string(child_sel)?;

    let js = if let Ok(idx) = iframe_sel.parse::<usize>() {
        format!("(() => {{ const f = ({}); const el = f && f.querySelector({}); if (el) el.click(); return !!el; }})()", js_get_frame(idx), child_json)
    } else {
        format!("(() => {{ const f = ({})(); const el = f && f.querySelector({}); if (el) el.click(); return !!el; }})()", js_get_frame_by_selector(iframe_sel), child_json)
    };

    let clicked: bool = page.eval::<bool>(&js).await.unwrap_or(false);
    println!("{{\"clicked\": {}}}", clicked);
    Ok(())
}

pub async fn action_iframe_fill(page: &Page, args: &CliArgs) -> Result<()> {
    let iframe_sel = args.selector.as_deref().ok_or_else(|| anyhow::anyhow!("No selector"))?;
    let child_sel = args.value.as_deref().ok_or_else(|| anyhow::anyhow!("No child selector"))?;
    let val = args.selector.as_deref().unwrap_or("");
    let val_json = serde_json::to_string(val)?;

    let js = if let Ok(_) = iframe_sel.parse::<usize>() {
        format!("(() => {{ const f = ({}); const el = f && f.querySelector({}); if (el) {{ el.value = {}; el.dispatchEvent(new Event('input', {{bubbles:true}})); return true; }} return false; }})()", js_get_frame(0), serde_json::to_string(child_sel)?, val_json)
    } else {
        format!("(() => {{ const f = ({})(); const el = f && f.querySelector({}); if (el) {{ el.value = {}; el.dispatchEvent(new Event('input', {{bubbles:true}})); return true; }} return false; }})()", js_get_frame_by_selector(iframe_sel), serde_json::to_string(child_sel)?, val_json)
    };

    let filled: bool = page.eval::<bool>(&js).await.unwrap_or(false);
    println!("{{\"filled\": {}}}", filled);
    Ok(())
}

pub async fn action_iframe_extract(page: &Page, args: &CliArgs) -> Result<()> {
    let sel = args.selector.as_deref().ok_or_else(|| anyhow::anyhow!("No selector"))?;
    let val = args.value.as_deref().unwrap_or("*");
    let val_json = serde_json::to_string(val)?;

    let js = if let Ok(idx) = sel.parse::<usize>() {
        format!("(() => {{ const f = ({}); return f ? Array.from(f.querySelectorAll({})).map(e => e.textContent.trim()) : []; }})()", js_get_frame(idx), val_json)
    } else {
        format!("(() => {{ const f = ({})(); return f ? Array.from(f.querySelectorAll({})).map(e => e.textContent.trim()) : []; }})()", js_get_frame_by_selector(sel), val_json)
    };

    let result: serde_json::Value = page.eval(&js).await?;
    println!("{}", serde_json::to_string_pretty(&result)?);
    Ok(())
}
