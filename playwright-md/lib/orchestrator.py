"""Orchestrator: Playwright navigate → extract HTML → sanitize → convert → Markdown."""

import json
import sys
from pathlib import Path

from bs4 import BeautifulSoup, Tag
from markdownify import markdownify

# ── HTML Utilities ──

STRIP_TAGS = {"script", "style", "noscript", "link", "meta"}


def sanitize_html(html: str) -> str:
    """Strip script, style, noscript tags from HTML."""
    soup = BeautifulSoup(html, "html.parser")
    for tag_name in STRIP_TAGS:
        for tag in soup.find_all(tag_name):
            tag.decompose()
    return str(soup)


def extract_sub_region(html: str, selector: str | None) -> str:
    """Extract sub-region by CSS selector. Returns full HTML if selector is None."""
    if selector is None:
        return html
    soup = BeautifulSoup(html, "html.parser")
    el = soup.select_one(selector)
    if el is None:
        return html  # fallback: return full if no match
    return str(el)


# ── Conversion ──


def html_to_markdown(html: str, backend: str = "markdownify") -> str:
    """Convert HTML string to Markdown."""
    if backend == "markdownify":
        return markdownify(html, heading_style="ATX", strip=["img"])
    elif backend == "html2text":
        import html2text

        h2t = html2text.HTML2Text()
        h2t.ignore_images = True
        return h2t.handle(html)
    else:
        raise ValueError(f"Unknown backend: {backend}")


# ── Post-Processing ──


def post_process_markdown(md: str) -> str:
    """Deduplicate blank lines, normalize trailing whitespace."""
    import re

    # Collapse 3+ blank lines → 2
    md = re.sub(r"\n{3,}", "\n\n", md)
    # Strip trailing whitespace per line
    md = "\n".join(line.rstrip() for line in md.split("\n"))
    return md.strip()


# ── Browser Pipeline ──


def run_page_to_md(
    url: str,
    output: str | None = None,
    wait_for: str | None = None,
    wait_for_url: str | None = None,
    timeout: int = 30000,
    retries: int = 1,
    selector: str | None = None,
    backend: str = "markdownify",
    cookies: str | None = None,
    headers: str | None = None,
    session_dir: str | None = None,
) -> int:
    """Full pipeline: navigate → wait → extract → sanitize → convert → output."""
    from playwright.sync_api import sync_playwright, Error as PlaywrightError

    last_error = None

    for attempt in range(1, retries + 1):
        try:
            with sync_playwright() as pw:
                browser = pw.chromium.launch(headless=True)

                # Build context with optional auth
                context_opts = {"user_agent": "playwright-md/0.1.0"}
                if session_dir:
                    sd = Path(session_dir)
                    state_file = sd / "storage_state.json"
                    if state_file.exists():
                        context_opts["storage_state"] = str(state_file)

                context = browser.new_context(**context_opts)

                # Inject cookies
                if cookies:
                    try:
                        cookie_list = json.loads(cookies)
                        context.add_cookies(cookie_list)
                    except json.JSONDecodeError:
                        print("Warning: invalid cookies JSON, skipping", file=sys.stderr)

                # Inject headers
                if headers:
                    try:
                        header_dict = json.loads(headers)
                        context.set_extra_http_headers(header_dict)
                    except json.JSONDecodeError:
                        print("Warning: invalid headers JSON, skipping", file=sys.stderr)

                page = context.new_page()

                # Navigate
                page.goto(url, timeout=timeout, wait_until="domcontentloaded")

                # Wait conditions
                if wait_for:
                    page.wait_for_selector(wait_for, timeout=timeout)
                if wait_for_url:
                    page.wait_for_url(wait_for_url, timeout=timeout)

                # Extract HTML
                raw_html = page.evaluate("document.documentElement.outerHTML")

                # Sub-region extraction
                html = extract_sub_region(raw_html, selector)

                # Sanitize
                html = sanitize_html(html)

                # Convert
                md = html_to_markdown(html, backend=backend)

                # Post-process
                md = post_process_markdown(md)

                # Output
                if output:
                    out_path = Path(output)
                    out_path.parent.mkdir(parents=True, exist_ok=True)
                    out_path.write_text(md, encoding="utf-8")
                    print(f"Written to {output}", file=sys.stderr)
                else:
                    print(md)

                # Save session state
                if session_dir:
                    sd = Path(session_dir)
                    sd.mkdir(parents=True, exist_ok=True)
                    state_file = sd / "storage_state.json"
                    state_file.write_text(
                        json.dumps(context.storage_state()), encoding="utf-8"
                    )

                context.close()
                browser.close()
                return 0

        except PlaywrightError as exc:
            last_error = exc
            print(f"Attempt {attempt}/{retries} failed: {exc}", file=sys.stderr)
            continue
        except KeyboardInterrupt:
            return 130

    # All retries exhausted
    if last_error:
        print(f"Error: all {retries} attempts failed: {last_error}", file=sys.stderr)
    return 1
