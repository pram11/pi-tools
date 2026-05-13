use anyhow::Result;
use playwright::api::page::Page;
use crate::actions::CliArgs;

pub async fn action_form_detect(page: &Page, _args: &CliArgs) -> Result<()> {
    let js = r#"() => {
        const nodes = document.querySelectorAll('input, textarea, select');
        const skip = new Set(['submit', 'button', 'hidden', 'image']);
        return Array.from(nodes)
            .filter(n => !skip.has(n.type))
            .map(n => ({
                tag: n.tagName.toLowerCase(),
                name: n.name || '',
                type: n.type || n.tagName.toLowerCase(),
                placeholder: n.placeholder || '',
                id: n.id || '',
                required: n.hasAttribute('required'),
            }));
    }"#;
    let result: serde_json::Value = page.eval(js).await?;
    println!("{}", serde_json::to_string_pretty(&result)?);
    Ok(())
}

pub async fn action_smart_fill(page: &Page, args: &CliArgs) -> Result<()> {
    let values: serde_json::Value = serde_json::from_str(
        args.value.as_deref().ok_or_else(|| anyhow::anyhow!("No JSON value"))?
    )?;
    let values_json = serde_json::to_string(&values)?;
    let js = format!(r#"
        (() => {{
            const values = {values_json};
            const results = [];
            for (const [name, val] of Object.entries(values)) {{
                const el = document.querySelector(`[name=${{name}}]`);
                if (!el) continue;
                if (el.type === 'checkbox' || el.type === 'radio') {{
                    el.checked = !!val;
                }} else if (el.tagName.toLowerCase() === 'select') {{
                    for (const o of el.options) {{
                        if (o.textContent.trim() === String(val) || o.value === String(val)) {{
                            el.value = o.value;
                            el.dispatchEvent(new Event('change', {{bubbles: true}}));
                            break;
                        }}
                    }}
                }} else {{
                    el.value = String(val);
                    el.dispatchEvent(new Event('input', {{bubbles: true}}));
                    el.dispatchEvent(new Event('change', {{bubbles: true}}));
                }}
                results.push(name);
            }}
            return results;
        }})()
    "#);
    let result: serde_json::Value = page.eval(&js).await?;
    println!("{{\"filled\": {}}}", result);
    Ok(())
}

pub async fn action_submit(page: &Page, args: &CliArgs) -> Result<()> {
    let sel = args.selector.as_deref().unwrap_or("input[type=submit], button[type=submit]");
    let _sel_json = serde_json::to_string(sel)?;
    let js = format!(
        r#"(sel) => {{ const el = document.querySelector(sel); return el && el.tagName === 'FORM'; }}"#,
    );
    let is_form: bool = page.eval::<bool>(&js).await.unwrap_or(false);

    if is_form {
        let js2 = format!(r#"(sel) => {{ const el = document.querySelector(sel); if (el) el.submit(); }}"#);
        page.eval::<()>(&js2).await?;
    } else {
        page.click_builder(sel).timeout(args.timeout as f64).click().await?;
    }

    println!("{{\"url\": \"{}\"}}", page.url()?);
    Ok(())
}

pub async fn action_wizard(page: &Page, args: &CliArgs) -> Result<()> {
    let steps: Vec<serde_json::Value> = serde_json::from_str(
        args.value.as_deref().ok_or_else(|| anyhow::anyhow!("No JSON steps"))?
    )?;
    let next_sel = args.selector.as_deref().unwrap_or(".next, button.next, [data-step-next]");

    let mut steps_filled = 0usize;
    let mut submitted = false;

    for step in &steps {
        if let Some(fields) = step.get("fields") {
            let fields_json = serde_json::to_string(fields)?;
            let js = format!(r#"
                (() => {{
                    const values = {fields_json};
                    for (const [name, val] of Object.entries(values)) {{
                        const el = document.querySelector(`[name=${{name}}]`);
                        if (el && el.type !== 'checkbox') el.value = String(val);
                    }}
                }})()
            "#);
            page.eval::<()>(&js).await.ok();
        }

        if step.get("submit").and_then(|v| v.as_bool()) == Some(true) {
            let submit_sel = step.get("next").and_then(|s| s.as_str()).unwrap_or("input[type=submit], button[type=submit]");
            page.click_builder(submit_sel).click().await.ok();
            submitted = true;
            steps_filled += 1;
            break;
        }

        let next_json = serde_json::to_string(next_sel)?;
        let js = format!(r#"
            (() => {{
                const sel = {next_json};
                const els = document.querySelectorAll(sel);
                for (const el of els) {{
                    const r = el.getBoundingClientRect();
                    if (r.width > 0 || r.height > 0) {{ el.click(); return; }}
                }}
            }})()
        "#);
        page.eval::<()>(&js).await.ok();
        steps_filled += 1;
    }

    println!("{{\"steps_filled\": {}, \"submitted\": {}}}", steps_filled, submitted);
    Ok(())
}
