#!/usr/bin/env python3
"""Playwright automation skill — CLI entry point."""

import argparse
import json
import sqlite3
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

# ── Session State (SQLite + storage_state JSON) ────────────────
SESSIONS_DIR = Path(__file__).parent / ".sessions"
DB_PATH = SESSIONS_DIR / "state.db"
STORAGE_PATH = SESSIONS_DIR / "storage.json"


def _get_conn() -> sqlite3.Connection:
    SESSIONS_DIR.mkdir(exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            url TEXT,
            title TEXT,
            cookies TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    return conn


def session_active() -> bool:
    """True if session DB row exists."""
    conn = _get_conn()
    row = conn.execute("SELECT 1 FROM sessions WHERE id = 1").fetchone()
    conn.close()
    return row is not None


def load_session() -> dict | None:
    conn = _get_conn()
    row = conn.execute("SELECT url, title, cookies FROM sessions WHERE id = 1").fetchone()
    conn.close()
    if row:
        return {"url": row[0], "title": row[1], "cookies": row[2]}
    return None


def save_session(data: dict):
    conn = _get_conn()
    conn.execute("""
        INSERT INTO sessions (id, url, title, cookies)
        VALUES (1, ?, ?, ?)
        ON CONFLICT(id) DO UPDATE SET url=excluded.url, title=excluded.title, cookies=excluded.cookies
    """, (data.get("url"), data.get("title"), json.dumps(data.get("cookies", []))))
    conn.commit()
    conn.close()


def save_storage_state(context):
    """Export cookies + localStorage to JSON file for persistence."""
    SESSIONS_DIR.mkdir(exist_ok=True)
    context.storage_state(path=str(STORAGE_PATH))


def load_storage_state():
    """Return storage_state path if exists, else None."""
    if STORAGE_PATH.exists():
        return str(STORAGE_PATH)
    return None


def clear_session():
    conn = _get_conn()
    conn.execute("DELETE FROM sessions WHERE id = 1")
    conn.commit()
    conn.close()
    if STORAGE_PATH.exists():
        STORAGE_PATH.unlink()


# ── Actions ─────────────────────────────────────────────────────

def _retry_navigation(page, browser, context, url, timeout_ms, max_retries):
    """Navigate with auto-recovery on timeout/crash. Returns True on success."""
    for attempt in range(1, max_retries + 1):
        try:
            page.goto(url, wait_until="domcontentloaded", timeout=timeout_ms)
            return True
        except Exception as e:
            err_msg = str(e).lower()
            if "timeout" in err_msg or "crash" in err_msg or "closed" in err_msg:
                if attempt < max_retries:
                    print(f"[recovery] Attempt {attempt} failed: {e}", file=sys.stderr)
                    # recreate page from context for recovery
                    try:
                        page.close()
                    except Exception:
                        pass
                    page = context.new_page()
                    continue
            raise
    return False


def action_navigate(page, args):
    page.goto(args.url, wait_until="domcontentloaded", timeout=args.timeout)
    print(f"[navigate] Loaded: {page.url}")


def action_navigate_retry(page, browser, context, args):
    """Navigate with auto-recovery. Replaces page if crash/timeout."""
    url = args.url or (load_session() or {}).get("url", "")
    if not url:
        raise ValueError("No URL for navigation")
    for attempt in range(1, args.retries + 1):
        try:
            page.goto(url, wait_until="domcontentloaded", timeout=args.timeout)
            print(f"[navigate] Loaded: {page.url}")
            return page
        except Exception as e:
            err_msg = str(e).lower()
            if "timeout" in err_msg or "crash" in err_msg or "closed" in err_msg:
                if attempt < args.retries:
                    print(f"[recovery] Attempt {attempt} failed: {e}", file=sys.stderr)
                    try:
                        page.close()
                    except Exception:
                        pass
                    page = context.new_page()
                    continue
            raise
    raise RuntimeError(f"Navigation failed after {args.retries} attempt(s)")


def action_click(page, args):
    page.click(args.selector)
    print(f"[click] Clicked: {args.selector}")


def action_type(page, args):
    page.fill(args.selector, args.value)
    print(f"[type] Filled {args.selector}: {args.value[:40]}")


def action_extract(page, args):
    text = page.text_content(args.selector) or ""
    print(text)


def action_screenshot(page, args):
    path = args.output or "screenshot.png"
    page.screenshot(path=path, full_page=True)
    print(f"[screenshot] Saved: {path}")


def action_wait(page, args):
    timeout = int(args.value or 5000)
    page.wait_for_selector(args.selector, timeout=timeout)
    print(f"[wait] Element found: {args.selector}")


def action_eval(page, args):
    result = page.evaluate(args.value)
    print(json.dumps(result, default=str))


def action_scroll(page, args):
    val = args.value or "top"
    if val == "top":
        page.evaluate("window.scrollTo(0, 0)")
    elif val == "bottom":
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
    else:
        page.evaluate(f"window.scrollTo(0, {int(val)})")
    print(f"[scroll] Scrolled to: {val}")


def detect_form_fields(page) -> list[dict]:
    """Auto-detect form fields (input, textarea, select). Excludes submit/button."""
    fields = page.evaluate("""
        () => {
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
        }
    """)
    return fields


def action_form_detect(page, args):
    fields = detect_form_fields(page)
    print(json.dumps(fields, indent=2))


ACTIONS = {
    "navigate": action_navigate,
    "click": action_click,
    "type": action_type,
    "extract": action_extract,
    "screenshot": action_screenshot,
    "wait": action_wait,
    "eval": action_eval,
    "scroll": action_scroll,
    "form-detect": action_form_detect,
}


# ── Session Commands ───────────────────────────────────────────

def session_start(args):
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()
        page.goto(args.url, wait_until="domcontentloaded")
        save_session({
            "url": page.url,
            "title": page.title(),
        })
        save_storage_state(context)
        print(f"[session] Started at: {page.url}")


def session_stop(args):
    clear_session()
    print("[session] Stopped.")


# ── Main ────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Playwright Skill")
    sub = parser.add_subparsers(dest="mode")

    # Session subcommands
    s_start = sub.add_parser("session-start", help="Start browser session")
    s_start.add_argument("--url", required=True)

    s_stop = sub.add_parser("session-stop", help="Stop browser session")

    # Direct action
    parser.add_argument("--url", help="Target URL")
    parser.add_argument("--action", choices=list(ACTIONS.keys()), help="Action to perform")
    parser.add_argument("--selector", help="CSS selector")
    parser.add_argument("--value", help="Value (type/eval/wait)")
    parser.add_argument("--output", help="Output file (screenshot)")
    parser.add_argument("--timeout", type=int, default=30000, help="Navigation timeout ms")
    parser.add_argument("--retries", type=int, default=1, help="Max retry attempts on crash/timeout")

    args = parser.parse_args()

    if args.mode == "session-start":
        session_start(args)
        return
    if args.mode == "session-stop":
        session_stop(args)
        return

    if not args.action:
        parser.print_help()
        sys.exit(1)

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)

        # Restore persistent storage if session active
        storage = load_storage_state()
        if storage and session_active():
            context = browser.new_context(storage_state=storage)
        else:
            context = browser.new_context()
        page = context.new_page()

        # Navigate with auto-recovery
        if args.action == "navigate":
            try:
                page = action_navigate_retry(page, browser, context, args)
            except Exception as e:
                print(f"[error] {e}", file=sys.stderr)
                browser.close()
                sys.exit(1)
        else:
            target_url = args.url or (load_session() or {}).get("url")
            if not target_url:
                print("[error] No URL provided and no active session", file=sys.stderr)
                browser.close()
                sys.exit(1)
            if not _retry_navigation(page, browser, context, target_url, args.timeout, args.retries):
                print(f"[error] Navigation failed after {args.retries} attempt(s)", file=sys.stderr)
                browser.close()
                sys.exit(1)

            try:
                ACTIONS[args.action](page, args)
                # Persist storage after successful action
                if session_active():
                    save_storage_state(context)
            except Exception as e:
                print(f"[error] {e}", file=sys.stderr)
                browser.close()
                sys.exit(1)

        browser.close()


if __name__ == "__main__":
    main()
