use anyhow::Result;
use playwright::api::page::Page;
use crate::actions::CliArgs;

pub async fn action_extract(page: &Page, args: &CliArgs) -> Result<()> {
    let sel = args.selector.as_deref().ok_or_else(|| anyhow::anyhow!("No selector"))?;
    let text = page.inner_text(sel, None).await.unwrap_or_default();
    println!("{text}");
    Ok(())
}

pub async fn action_scrape(page: &Page, args: &CliArgs) -> Result<()> {
    let sel = args.selector.as_deref().ok_or_else(|| anyhow::anyhow!("No selector"))?;
    let fmt = args.value.as_deref().unwrap_or("json");

    let js = format!(r#"
        (() => {{
            const table = document.querySelector({sel_json});
            if (!table) return [];
            const thead = table.querySelector('thead tr');
            const headers = thead
                ? Array.from(thead.querySelectorAll('th, td')).map(h => h.textContent.trim())
                : [];
            const rows = Array.from(table.querySelectorAll('tbody tr, tr'))
                .filter(tr => !thead || !thead.contains(tr));
            return rows.map((tr, idx) => {{
                const cells = Array.from(tr.querySelectorAll('td, th')).map(c => c.textContent.trim());
                if (headers.length) {{
                    const obj = {{}};
                    headers.forEach((h, i) => obj[h] = cells[i] || '');
                    return obj;
                }} else {{
                    const obj = {{}};
                    cells.forEach((c, i) => obj[`col_${{i + 1}}`] = c);
                    return obj;
                }}
            }});
        }})()
    "#, sel_json = serde_json::to_string(sel)?);

    let result: serde_json::Value = page.eval(&js).await?;

    if let Some(arr) = result.as_array() {
        if fmt == "csv" && !arr.is_empty() {
            print_csv(arr);
        } else {
            println!("{}", serde_json::to_string_pretty(&result)?);
        }
    } else {
        println!("{}", serde_json::to_string_pretty(&result)?);
    }
    Ok(())
}

fn print_csv(rows: &[serde_json::Value]) {
    if rows.is_empty() { return; }
    let headers: Vec<String> = rows[0].as_object().map(|m| m.keys().cloned().collect()).unwrap_or_default();
    println!("{}", headers.join(","));
    for row in rows {
        let vals: Vec<String> = headers.iter().map(|h| {
            row.get(h).map(|v| v.to_string()).unwrap_or_default()
        }).collect();
        println!("{}", vals.join(","));
    }
}

pub async fn action_extract_all(page: &Page, args: &CliArgs) -> Result<()> {
    let parent = args.selector.as_deref().ok_or_else(|| anyhow::anyhow!("No parent selector"))?;
    let child = args.value.as_deref().ok_or_else(|| anyhow::anyhow!("No child selector"))?;

    let js = if let Ok(map) = serde_json::from_str::<std::collections::HashMap<String, String>>(child) {
        let pairs_json = serde_json::to_string(&map)?;
        format!(r#"
            (() => {{
                const childMap = {pairs_json};
                const parents = document.querySelectorAll({parent_json});
                return Array.from(parents).map(el => {{
                    const obj = {{}};
                    for (const [sel, key] of Object.entries(childMap)) {{
                        const found = el.querySelector(sel);
                        obj[key] = found ? found.textContent.trim() : '';
                    }}
                    return obj;
                }});
            }})()
        "#, parent_json = serde_json::to_string(parent)?)
    } else {
        format!(r#"
            (() => {{
                const parents = document.querySelectorAll({parent_json});
                const childSel = {child_json};
                const all = [];
                for (const parent of parents) {{
                    const children = parent.querySelectorAll(childSel);
                    for (const el of children) {{
                        all.push(el.textContent.trim());
                    }}
                }}
                return all;
            }})()
        "#, parent_json = serde_json::to_string(parent)?, child_json = serde_json::to_string(child)?)
    };

    let result: serde_json::Value = page.eval(&js).await?;
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
