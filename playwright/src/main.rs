mod actions;
mod session;
mod utils;

use anyhow::Result;
use clap::{Parser, Subcommand};
use actions::{CliArgs, dispatch};
use playwright::Playwright;
use playwright::api::browser_context::BrowserContext;
use playwright::api::browser::Browser;
use playwright::api::page::Page;

#[derive(Parser)]
#[command(name = "playwright", about = "Headless Chromium automation CLI")]
struct Cli {
    #[command(subcommand)]
    mode: Option<Mode>,

    #[command(flatten)]
    args: CliArgs,

    /// Action to perform
    #[arg()]
    action: Option<String>,
}

#[derive(Subcommand)]
enum Mode {
    /// Start browser session
    SessionStart {
        #[arg(long)]
        url: String,
    },
    /// Stop browser session
    SessionStop,
}

#[tokio::main]
async fn main() -> Result<()> {
    env_logger::init();
    let cli = Cli::parse();

    match &cli.mode {
        Some(Mode::SessionStart { url }) => {
            session_start(url).await?;
            return Ok(());
        }
        Some(Mode::SessionStop) => {
            session::clear_session()?;
            println!("[session] Stopped.");
            return Ok(());
        }
        None => {}
    }

    let action = match cli.action.as_deref() {
        Some(a) => a.to_string(),
        None => {
            eprintln!("No action specified. Use --help for usage.");
            std::process::exit(1);
        }
    };

    let (browser, context, page) = launch_browser(&cli.args).await?;
    let result = dispatch(&action, &cli.args, &browser, &context, page).await;

    // Persist storage after successful action
    if result.is_ok() && session::session_active() {
        let sp = session::storage_path();
        if let Ok(state) = context.storage_state().await {
            std::fs::write(&sp, serde_json::to_string(&state).unwrap_or_default()).ok();
        }
    }

    if let Err(e) = result {
        eprintln!("[error] {e}");
        browser.close().await.ok();
        std::process::exit(1);
    }

    browser.close().await.ok();
    Ok(())
}

async fn launch_browser(args: &CliArgs) -> Result<(Browser, BrowserContext, Page)> {
    let pw = Playwright::initialize().await?;
    let browser = pw.chromium().launcher().headless(true).launch().await?;
    let context = browser.context_builder().build().await?;
    let page = context.new_page().await?;

    let url = args.url.clone().or_else(|| session::load_session().map(|s| s.url));
    if let Some(ref target_url) = url {
        navigate_with_retry(&page, target_url, args.retries, args.timeout).await?;
    }

    Ok((browser, context, page))
}

async fn navigate_with_retry(page: &Page, url: &str, retries: usize, timeout: u64) -> Result<()> {
    let mut last_err = anyhow::anyhow!("No attempts made");
    for i in 0..=retries {
        match page.goto_builder(url)
            .timeout(timeout as f64)
            .goto().await {
            Ok(_) => return Ok(()),
            Err(e) => {
                last_err = anyhow::anyhow!("{}: {}", e, if i < retries { "retrying..." } else { "giving up" });
                if i < retries {
                    tokio::time::sleep(std::time::Duration::from_millis(100 * (1 << i))).await;
                }
            }
        }
    }
    Err(last_err)
}

async fn session_start(url: &str) -> Result<()> {
    let pw = Playwright::initialize().await?;
    let browser = pw.chromium().launcher().headless(true).launch().await?;
    let context = browser.context_builder().build().await?;
    let page = context.new_page().await?;
    page.goto_builder(url).goto().await?;

    let page_url = page.url()?;
    let title = page.title().await?;
    session::save_session(&page_url, &title, "[]")?;

    let sp = session::storage_path();
    let state = context.storage_state().await?;
    std::fs::write(&sp, serde_json::to_string(&state).unwrap_or_default())?;

    println!("[session] Started at: {}", page.url()?);
    browser.close().await?;
    Ok(())
}
