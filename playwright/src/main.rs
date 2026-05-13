mod actions;
mod session;
mod utils;

use anyhow::Result;
use clap::{Parser, Subcommand};
use actions::{CliArgs, dispatch};

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

    let action = cli.action.as_deref().ok_or_else(|| {
        eprintln!("No action specified. Use --help for usage.");
        std::process::exit(1);
    })?;

    let browser = playwright::Playwright::new().await?.with_chromium().headless(true).launch().await?;

    // Restore persistent storage if session active
    let context = if session::session_active() {
        if let Some(storage_path) = session::storage_state_path() {
            let storage_str = std::fs::read_to_string(&storage_path).ok();
            browser.new_context()
                .storage_state_path(storage_path.to_str().unwrap_or(""))
                .await?
        } else {
            browser.new_context().await?
        }
    } else {
        browser.new_context().await?
    };

    let page = context.new_page().await?;

    // Navigate with auto-recovery
    let url = cli.args.url.clone().or_else(|| session::load_session().map(|s| s.url));
    if let Some(ref target_url) = url {
        if let Err(e) = utils::retry(cli.args.retries, || async {
            page.goto(target_url)
                .wait_until(playwright::types::WaitUntil::DomContentLoaded)
                .timeout(cli.args.timeout)
                .await
        }).await {
            eprintln!("[error] Navigation failed: {e}");
            browser.close().await.ok();
            std::process::exit(1);
        }
    }

    // Dispatch action
    let result = dispatch(action, &cli.args, &browser).await;

    // Persist storage after successful action
    if result.is_ok() && session::session_active() {
        let sp = session::storage_path();
        context.storage_state().await.map(|state| {
            std::fs::write(&sp, serde_json::to_string(&state).unwrap_or_default).ok();
        }).ok();
    }

    if let Err(e) = result {
        eprintln!("[error] {e}");
        browser.close().await.ok();
        std::process::exit(1);
    }

    browser.close().await?;
    Ok(())
}

async fn session_start(url: &str) -> Result<()> {
    let pw = playwright::Playwright::new().await?;
    let browser = pw.with_chromium().headless(true).launch().await?;
    let context = browser.new_context().await?;
    let page = context.new_page().await?;
    page.goto(url).wait_until(playwright::types::WaitUntil::DomContentLoaded).await?;

    session::save_session(&page.url().await, &page.title().await, "[]")?;

    // Save storage state
    let sp = session::storage_path();
    let state = context.storage_state().await?;
    std::fs::write(&sp, serde_json::to_string(&state).unwrap_or_default)?;

    println!("[session] Started at: {}", page.url().await);
    browser.close().await?;
    Ok(())
}
