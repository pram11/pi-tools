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


# ── Phase 4: Network Interception ─────────────────────────────

def capture_network(page, url: str) -> list[dict]:
    """Navigate to URL, capture all network responses.

    Returns list of dicts: {url, status, headers, body}
    """
    captured = []

    def _on_response(response):
        try:
            body = response.text()
        except Exception:
            body = ""
        captured.append({
            "url": response.url,
            "status": response.status,
            "headers": response.headers,
            "body": body,
        })

    page.on("response", _on_response)
    page.goto(url, wait_until="networkidle", timeout=30000)
    page.remove_listener("response", _on_response)
    return captured


def action_network(page, args, browser=None, context=None):
    """CLI action: capture network responses during page load."""
    url = args.url
    if not url:
        raise ValueError("--url required for network capture")
    responses = capture_network(page, url)
    print(json.dumps(responses, indent=2, default=str))


# ── Phase 4: Data Extraction ──────────────────────────────────

def scrape_table(page, selector: str, fmt: str = "json") -> list | str:
    """Scrape HTML table into structured data.

    Args:
        page: Playwright page.
        selector: CSS selector targeting the <table>.
        fmt: "json" (list[dict]) or "csv" (string).

    Returns:
        list of dicts (json) or CSV string.
    """
    result = page.evaluate("""
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
    """, selector)

    if fmt == "csv" and result:
        import csv
        import io
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=result[0].keys(), lineterminator="\n")
        writer.writeheader()
        writer.writerows(result)
        return output.getvalue()

    return result


def action_scrape(page, args):
    """CLI action: scrape table → JSON/CSV."""
    fmt = args.value or "json"
    result = scrape_table(page, args.selector, fmt=fmt)
    if isinstance(result, str):
        print(result, end="")
    else:
        print(json.dumps(result, indent=2))


def extract_all(page, parent_selector: str, child: str | dict, nth: int = None) -> list:
    """Repeatable / recursive extraction from repeated DOM blocks.

    Args:
        page: Playwright page.
        parent_selector: CSS selector for repeated container elements.
        child: CSS sub-selector (str) for flat extraction, or dict mapping
               {selector: key_name} for recursive (nested) extraction.
        nth: Optional 0-based index to extract only one item.

    Returns:
        List of strings (flat) or list of dicts (recursive).
    """
    if isinstance(child, dict):
        # Recursive: extract multiple sub-fields per parent
        result = page.evaluate("""
            (params) => {
                const parents = document.querySelectorAll(params.parentSel);
                return Array.from(parents).map(el => {
                    const obj = {};
                    for (const [sel, key] of Object.entries(params.childMap)) {
                        const found = el.querySelector(sel);
                        obj[key] = found ? found.textContent.trim() : '';
                    }
                    return obj;
                });
            }
        """, {"parentSel": parent_selector, "childMap": child})
    else:
        # Flat: extract all matching sub-elements across parent blocks
        result = page.evaluate("""
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
        """, {"parentSel": parent_selector, "childSel": child})

    if nth is not None:
        result = result[nth:nth + 1]

    return result


def action_extract_all(page, args):
    """CLI action: extract repeated / nested elements."""
    nth = int(args.nth) if args.nth is not None else None
    try:
        child = json.loads(args.value)
    except (json.JSONDecodeError, TypeError):
        child = args.value  # plain CSS selector
    result = extract_all(page, args.selector, child, nth=nth)
    print(json.dumps(result, indent=2))


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


def smart_fill(page, values: dict) -> list[str]:
    """Map field names→values. Fills input/textarea/select/checkbox by [name].
    Returns list of successfully filled field names."""
    if not values:
        return []
    filled = page.evaluate("""
        (values) => {
            const results = [];
            for (const [name, val] of Object.entries(values)) {
                const el = document.querySelector(`[name=${name}]`);
                if (!el) continue;
                if (el.type === 'checkbox' || el.type === 'radio') {
                    el.checked = !!val;
                } else if (el.tagName.toLowerCase() === 'select') {
                    const opt = el.querySelector(`option[value=${val}]`) || el.querySelector(`option`);
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
    """, values)
    return filled


def action_smart_fill(page, args):
    """Fill form fields from JSON string in --value."""
    try:
        values = json.loads(args.value)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON for smart-fill: {e}")
    filled = smart_fill(page, values)
    print(json.dumps({"filled": filled}, indent=2))


def form_submit(page, selector: str = None, timeout: int = 30000) -> dict:
    """Submit form by clicking button or form element.
    Waits for navigation/response after submission.
    Returns dict with url after submit."""
    if not selector:
        selector = "input[type=submit], button[type=submit]"

    # Determine if selector is a form element or submit button
    is_form = page.eval_on_selector(selector, "el => el.tagName === 'FORM'")

    if is_form:
        # Submit form element directly
        page.eval_on_selector(selector, "el => el.submit()")
    else:
        # Click submit button/input
        page.click(selector, timeout=timeout)

    # Wait for navigation or load event
    try:
        page.wait_for_load_state("load", timeout=timeout)
    except Exception:
        pass  # Navigation may not occur if form uses AJAX

    return {"url": page.url}


def action_submit(page, args):
    """CLI action for form submit."""
    selector = args.selector or "input[type=submit], button[type=submit]"
    result = form_submit(page, selector=selector, timeout=args.timeout)
    print(json.dumps(result, indent=2))


def wizard_fill(page, steps: list[dict], next_selector: str = ".next, button.next, [data-step-next]", timeout: int = 30000) -> dict:
    """Fill multi-step wizard form.

    Each step: {"fields": {name: val, ...}, "next": selector_or_None, "submit": bool}
    Fills fields, clicks next (or submit), repeats.
    Returns {"steps_filled": int, "submitted": bool}.
    """
    steps_filled = 0
    submitted = False

    for step in steps:
        fields = step.get("fields", {})
        if fields:
            smart_fill(page, fields)

        is_submit = step.get("submit", False)
        if is_submit:
            submit_sel = step.get("next", "input[type=submit], button[type=submit]")
            try:
                page.locator(submit_sel).filter(visible=True).first.click(timeout=timeout)
            except Exception:
                page.eval_on_selector("form", "el => el.submit()")
            submitted = True
            steps_filled += 1
            break

        nxt = step.get("next", next_selector)
        if nxt:
            # Use JS dispatch to click visible element (handles hidden sibling buttons)
            page.evaluate("""
                (sel) => {
                    const els = document.querySelectorAll(sel);
                    for (const el of els) {
                        const r = el.getBoundingClientRect();
                        if (r.width > 0 || r.height > 0) {
                            el.click();
                            return;
                        }
                    }
                    throw new Error('No visible element: ' + sel);
                }
            """, nxt)
        steps_filled += 1

    return {"steps_filled": steps_filled, "submitted": submitted}


def action_wizard(page, args):
    """CLI action for wizard multi-step form fill."""
    try:
        steps = json.loads(args.value)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON for wizard steps: {e}")
    next_sel = args.selector or ".next, button.next, [data-step-next]"
    result = wizard_fill(page, steps, next_selector=next_sel, timeout=args.timeout)
    print(json.dumps(result, indent=2))


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
    "smart-fill": action_smart_fill,
    "submit": action_submit,
    "wizard": action_wizard,
    "scrape": action_scrape,
    "extract-all": action_extract_all,
    "network": action_network,
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
    parser.add_argument("--nth", type=int, default=None, help="Nth item index (0-based) for extract-all")

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
        elif args.action == "network":
            try:
                action_network(page, args, browser=browser, context=context)
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
