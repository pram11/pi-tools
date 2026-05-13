use anyhow::Result;
use playwright::Page;
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
    let result: serde_json::Value = page.evaluate(js).await?;
    println!("{}", serde_json::to_string_pretty(&result)?);
    Ok(())
}

pub async fn action_smart_fill(page: &Page, args: &CliArgs) -> Result<()> {
    let values: serde_json::Value = serde_json::from_str(
        args.value.as_deref().ok_or_else(|| anyhow::anyhow!("No JSON value"))?
    )?;
    let js = r#"
        (values) => {
            const results = [];
            for (const [name, val] of Object.entries(values)) {
                const el = document.querySelector(`[name=${name}]`);
                if (!el) continue;
                if (el.type === 'checkbox' || el.type === 'radio') {
                    el.checked = !!val;
                } else if (el.tagName.toLowerCase() === 'select') {
                    const opt = el.querySelector(`option[value=${val}]`) || el.querySelector('option');
                    for (const o of el.options) {
                        if (o.textContent.trim() === String(val) || o.value === String(val)) {
                            el.value = o.value;
                            el.dispatchEvent(new Event('change', {bubbles: true}));
                            break;
                        }
                    }
                } else {
                    el.value = String(val);
                    el.dispatchEvent(new Event('input', {bubbles: true}));
                    el.dispatchEvent(new Event('change', {bubbles: true}));
                }
                results.push(name);
            }
            return results;
        }
    "#;
    let result: serde_json::Value = page.evaluate(&format!("({js})", values = serde_json::to_value(&values)?)).await?;
    println!("{{\"filled\": {}}}", result);
    Ok(())
}

pub async fn action_submit(page: &Page, args: &CliArgs) -> Result<()> {
    let sel = args.selector.as_deref().unwrap_or("input[type=submit], button[type=submit]");
    let is_form: bool = page.evaluate(&format!(
        r#"(sel) => {{ const el = document.querySelector(sel); return el && el.tagName === 'FORM'; }}"#,
        sel = sel
    )).await.unwrap_or(false);

    if is_form {
        page.evaluate(&format!(r#"(sel) => document.querySelector(sel).submit()"#, sel = sel)).await?;
    } else {
        page.click(sel).timeout(args.timeout).await?;
    }

    println!("{{\"url\": \"{}\"}}", page.url().await);
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
            // Smart fill fields
            let js = r#"
                (values) => {
                    for (const [name, val] of Object.entries(values)) {
                        const el = document.querySelector(`[name=${name}]`);
                        if (el && el.type !== 'checkbox') el.value = String(val);
                    }
                }
            "#;
            page.evaluate(&format!("({js})", values = fields)).await.ok();
        }

        if step.get("submit").map(|v| v.as_bool()).unwrap_or(false) {
            let submit_sel = step.get("next").map(|s| s.as_str().unwrap_or("input[type=submit], button[type=submit]"));
            page.click(submit_sel).await.ok();
            submitted = true;
            steps_filled += 1;
            break;
        }

        // Click next button
        let js = format!(r#"
            (sel) => {{
                const els = document.querySelectorAll(sel);
                for (const el of els) {{
                    const r = el.getBoundingClientRect();
                    if (r.width > 0 || r.height > 0) {{ el.click(); return; }}
                }}
            }}
        "#);
        page.evaluate(&js).await.ok();
        steps_filled += 1;
    }

    println!("{{\"steps_filled\": {}, \"submitted\": {}}}", steps_filled, submitted);
    Ok(())
}
