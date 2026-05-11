#!/usr/bin/env python3
"""Playwright automation skill — CLI entry point."""

import argparse
import json
import sqlite3
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

# ── Session State (SQLite) ─────────────────────────────────────
DB_PATH = Path(__file__).parent / ".sessions" / "state.db"


def _get_conn() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(exist_ok=True)
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


def clear_session():
    conn = _get_conn()
    conn.execute("DELETE FROM sessions WHERE id = 1")
    conn.commit()
    conn.close()


# ── Actions ─────────────────────────────────────────────────────

def action_navigate(page, args):
    page.goto(args.url, wait_until="domcontentloaded")
    print(f"[navigate] Loaded: {page.url}")


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


ACTIONS = {
    "navigate": action_navigate,
    "click": action_click,
    "type": action_type,
    "extract": action_extract,
    "screenshot": action_screenshot,
    "wait": action_wait,
    "eval": action_eval,
    "scroll": action_scroll,
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
        page = browser.new_page()

        # If no URL, try session state
        if args.url:
            page.goto(args.url, wait_until="domcontentloaded")
        elif args.action != "navigate" and load_session():
            page.goto(load_session()["url"], wait_until="domcontentloaded")
        elif not args.url and args.action != "navigate":
            print("[error] No URL provided and no active session", file=sys.stderr)
            browser.close()
            sys.exit(1)

        try:
            ACTIONS[args.action](page, args)
        except Exception as e:
            print(f"[error] {e}", file=sys.stderr)
            browser.close()
            sys.exit(1)

        browser.close()


if __name__ == "__main__":
    main()
