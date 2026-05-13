use anyhow::Result;
use playwright::api::page::Page;
use std::fs;
use std::path::Path;
use crate::actions::CliArgs;

pub async fn action_screenshot(page: &Page, args: &CliArgs) -> Result<()> {
    let path = args.output.as_deref().unwrap_or("screenshot.png");
    let data: Vec<u8> = page.screenshot_builder()
        .full_page(true)
        .screenshot().await?;
    fs::write(path, &data)?;
    println!("[screenshot] Saved: {path}");
    Ok(())
}

pub async fn action_screenshot_diff(page: &Page, args: &CliArgs) -> Result<()> {
    let baseline = args.baseline.as_deref().ok_or_else(|| anyhow::anyhow!("No baseline"))?;
    let actual = args.output.as_deref().unwrap_or("actual.png");
    let threshold: f64 = args.value.as_deref().unwrap_or("0.95").parse()?;

    if !Path::new(actual).exists() {
        let data: Vec<u8> = page.screenshot_builder().full_page(true).screenshot().await?;
        fs::write(actual, &data)?;
    }

    let result = diff_screenshots(baseline, actual, threshold)?;
    println!("{}", serde_json::to_string_pretty(&result)?);
    Ok(())
}

pub fn diff_screenshots(
    baseline_path: &str,
    actual_path: &str,
    threshold: f64,
) -> Result<serde_json::Value> {
    if !Path::new(baseline_path).exists() {
        anyhow::bail!("Baseline not found: {baseline_path}");
    }
    if !Path::new(actual_path).exists() {
        anyhow::bail!("Actual not found: {actual_path}");
    }

    let img_a = image::open(baseline_path)?.to_rgb8();
    let img_b = image::open(actual_path)?.to_rgb8();

    let (w, h) = img_a.dimensions();
    let img_b = if img_b.dimensions() != (w, h) {
        image::imageops::resize(&img_b, w, h, image::imageops::FilterType::Lanczos3)
    } else {
        img_b
    };

    let total = (w * h) as usize;
    let mut diff_count = 0usize;

    // Build diff image as raw buffer
    let mut diff_buf = vec![0u8; (w * h * 3) as usize];
    for (idx, (&a, &b)) in img_a.pixels().zip(img_b.pixels()).enumerate() {
        let offset = idx * 3;
        if a != b {
            diff_count = diff_count.saturating_add(1);
            diff_buf[offset..offset+3].copy_from_slice(&[255, 0, 0]);
        }
    }

    let diff_img = image::RgbImage::from_raw(w, h, diff_buf)
        .ok_or_else(|| anyhow::anyhow!("Failed to create diff image"))?;

    let similarity = 1.0 - (diff_count as f64 / total as f64);
    let diff_path = format!("screenshot_diff_{:x}.png", std::time::SystemTime::now()
        .duration_since(std::time::UNIX_EPOCH)
        .unwrap()
        .as_millis());
    diff_img.save(&diff_path)?;

    Ok(serde_json::json!({
        "similarity": (similarity * 10000.0).round() / 10000.0,
        "match": similarity >= threshold,
        "diff_path": diff_path,
        "diff_pixels": diff_count,
    }))
}
