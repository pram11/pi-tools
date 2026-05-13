use anyhow::Result;
use playwright::Page;
use crate::actions::CliArgs;

pub async fn action_extract(page: &Page, args: &CliArgs) -> Result<()> {
    let sel = args.selector.as_deref().ok_or_else(|| anyhow::anyhow!("No selector"))?;
    let text = page.inner_text(sel).await.unwrap_or_default();
    println!("{text}");
    Ok(())
}

pub async fn action_scrape(page: &Page, args: &CliArgs) -> Result<()> {
    let sel = args.selector.as_deref().ok_or_else(|| anyhow::anyhow!("No selector"))?;
    let fmt = args.value.as_deref().unwrap_or("json");

    let js = r#"
        (selector) => {
            const table = document.querySelector(selector);
            if (!table) return [];
            const thead = table.querySelector('thead tr');
            const headers = thead
                ? Array.from(thead.querySelectorAll('th, td')).map(h => h.textContent.trim())
                : [];
            const rows = Array.from(table.querySelectorAll('tbody tr, tr'))
                .filter(tr => !thead || !thead.contains(tr));
            return rows.map((tr, idx) => {
                const cells = Array.from(tr.querySelectorAll('td, th')).map(c => c.textContent.trim());
                if (headers.length) {
                    const obj = {};
                    headers.forEach((h, i) => obj[h] = cells[i] || '');
                    return obj;
                } else {
                    const obj = {};
                    cells.forEach((c, i) => obj[`col_${i + 1}`] = c);
                    return obj;
                }
            });
        }
    "#;
    let result: serde_json::Value = page.evaluate_handle(&format!("({js})", selector = sel)).await?;
    let result: Vec<serde_json::Value> = page.evaluate(&format!("({js})", selector = sel)).await?;

    if fmt == "csv" && !result.is_empty() {
        let json_val: Vec<serde_json::Value> = serde_json::from_value(serde_json::to_value(&result)?)?;
        print_csv(&json_val);
    } else {
        println!("{}", serde_json::to_string_pretty(&result)?);
    }
    Ok(())
}

fn print_csv(rows: &[serde_json::Value]) {
    if rows.is_empty() { return; }
    let headers: Vec<&str> = rows[0].as_object().map(|m| m.keys().collect()).unwrap_or_default();
    println!("{}", headers.join(","));
    for row in rows {
        let vals: Vec<String> = headers.iter().map(|h| {
            row.get(*h).map(|v| v.to_string()).unwrap_or_default()
        }).collect();
        println!("{}", vals.join(","));
    }
}

pub async fn action_extract_all(page: &Page, args: &CliArgs) -> Result<()> {
    let parent = args.selector.as_deref().ok_or_else(|| anyhow::anyhow!("No parent selector"))?;
    let child = args.value.as_deref().ok_or_else(|| anyhow::anyhow!("No child selector"))?;

    let js = if let Ok(map) = serde_json::from_str::<std::collections::HashMap<String, String>>(child) {
        // Recursive: {selector: key}
        let pairs: Vec<_> = map.into_iter().collect();
        format!(r#"
            (params) => {{
                const parents = document.querySelectorAll(params.parentSel);
                return Array.from(parents).map(el => {{
                    const obj = {{}};
                    for (const [sel, key] of Object.entries(params.childMap)) {{
                        const found = el.querySelector(sel);
                        obj[key] = found ? found.textContent.trim() : '';
                    }}
                    return obj;
                }});
            }}
        "#)
    } else {
        // Flat: CSS sub-selector
        r#"
            (params) => {
                const parents = document.querySelectorAll(params.parentSel);
                const all = [];
                for (const parent of parents) {
                    const children = parent.querySelectorAll(params.childSel);
                    for (const el of children) {
                        all.push(el.textContent.trim());
                    }
                }
                return all;
            }
        "#
        .to_string()
    };

    let result: serde_json::Value = page.evaluate(&js).await?;
    if let Some(nth) = args.nth {
        if let Some(arr) = result.as_array() {
            let sliced = if nth < arr.len() { &arr[nth..] } else { &[] };
            println!("{}", serde_json::to_string_pretty(&sliced)?);
        }
    } else {
        println!("{}", serde_json::to_string_pretty(&result)?);
    }
    Ok(())
}
