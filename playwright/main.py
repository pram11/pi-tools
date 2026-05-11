#!/usr/bin/env python3
"""Playwright automation skill — CLI entry point."""

import argparse
import json
import os
import sqlite3
import sys
import time
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


# ── Phase 5: Screenshot Diffing (Visual Regression) ────────────

def diff_screenshots(
    baseline_path: str,
    actual_path: str,
    *,
    threshold: float = 0.95,
    diff_path: str | None = None,
) -> dict:
    """Compare two screenshots pixel-by-pixel.

    Args:
        baseline_path: Path to expected/reference screenshot.
        actual_path: Path to new/current screenshot.
        threshold: Similarity ratio (0.0–1.0) for pass/fail. Default 0.95.
        diff_path: Optional output path for diff image. Auto-generated if None.

    Returns:
        Dict with:
            - similarity: float (0.0–1.0)
            - match: bool (similarity >= threshold)
            - diff_path: path to generated diff image
            - diff_pixels: count of differing pixels
    """
    import numpy as np
    from PIL import Image

    if not os.path.exists(baseline_path):
        raise ValueError(f"Baseline screenshot not found: {baseline_path}")
    if not os.path.exists(actual_path):
        raise ValueError(f"Actual screenshot not found: {actual_path}")

    if diff_path is None:
        import uuid
        diff_path = f"screenshot_diff_{uuid.uuid4().hex[:8]}.png"

    img_a = Image.open(baseline_path).convert("RGB")
    img_b = Image.open(actual_path).convert("RGB")

    # Resize to match if different sizes
    sizes_match = img_a.size == img_b.size
    if not sizes_match:
        img_b = img_b.resize(img_a.size, Image.LANCZOS)

    # Numpy array comparison (avoids PIL getdata deprecation)
    arr_a = np.asarray(img_a)
    arr_b = np.asarray(img_b)
    diff_mask = arr_a != arr_b
    total_pixels = arr_a.shape[0] * arr_a.shape[1]
    diff_count = int(np.any(diff_mask, axis=2).sum())
    similarity = 1.0 - (diff_count / total_pixels) if total_pixels else 1.0

    # Generate diff image (red for diffs, black for matches)
    diff_img = Image.new("RGB", img_a.size, (0, 0, 0))
    diff_arr = np.array(np.asarray(diff_img))  # writable copy
    diff_arr[np.any(diff_mask, axis=2)] = [255, 0, 0]
    Image.fromarray(diff_arr).save(diff_path)

    return {
        "similarity": round(similarity, 4),
        "match": similarity >= threshold,
        "diff_path": diff_path,
        "diff_pixels": diff_count,
        "size_mismatch": not sizes_match,
    }


def action_screenshot_diff(page, args):
    """CLI action: compare baseline vs actual screenshot."""
    baseline = args.baseline
    actual = args.output or "actual.png"
    # Capture actual if file doesn't exist yet
    if not os.path.exists(actual):
        page.screenshot(path=actual, full_page=True)
    threshold = float(args.value) if args.value else 0.95
    result = diff_screenshots(baseline, actual, threshold=threshold)
    print(json.dumps(result, indent=2))


# ── Phase 5: Wait-for-Conditions ─────────────────────────────────

def wait_network_idle(page, idle_timeout: int = 1000) -> bool:
    """Block until no network requests for idle_timeout ms.

    Args:
        page: Playwright page.
        idle_timeout: Milliseconds of idle to wait (default 1000).

    Returns:
        True when idle.

    Raises:
        TimeoutError if idle never achieved within page timeout.
    """
    page.wait_for_load_state("networkidle", timeout=idle_timeout + 5000)  # type: ignore
    return True


def wait_element_state(page, selector: str, state: str, timeout: int = 5000) -> bool:
    """Block until element reaches specified state.

    Args:
        page: Playwright page.
        selector: CSS selector.
        state: One of 'visible', 'hidden', 'attached', 'detached'.
        timeout: Max wait in ms.

    Returns:
        True when state achieved.

    Raises:
        Exception on timeout.
    """
    valid_states = ("visible", "hidden", "attached", "detached")
    if state not in valid_states:
        raise ValueError(f"wait-element-state: invalid state '{state}'. Must be one of {valid_states}")
    page.wait_for_selector(selector, state=state, timeout=timeout)
    return True


def wait_http_status(page, expected_status: int, timeout: int = 5000, url: str | None = None) -> bool:
    """Block until a response with expected HTTP status is received.

    Args:
        page: Playwright page.
        expected_status: HTTP status code to wait for.
        timeout: Max wait in ms.
        url: Optional URL to navigate to (listener attached before nav).

    Returns:
        True when status matched.

    Raises:
        TimeoutError if status never received within timeout.
    """
    matched = False

    def _on_response(response):
        nonlocal matched
        if response.status == expected_status:
            matched = True

    page.on("response", _on_response)

    # Navigate if url provided (listener already attached)
    if url:
        page.goto(url, wait_until="domcontentloaded", timeout=timeout)

    deadline = time.time() + timeout / 1000
    while time.time() < deadline:
        if matched:
            page.remove_listener("response", _on_response)
            return True
        time.sleep(0.05)

    page.remove_listener("response", _on_response)
    raise TimeoutError(f"wait-http-status: expected {expected_status}, never received within {timeout}ms")


# ── Phase 5: Assertions ─────────────────────────────────────────

def assert_text(page, selector: str, expected: str) -> bool:
    """Verify element text contains expected string. Raises AssertionError on mismatch."""
    try:
        text = (page.text_content(selector, timeout=5000) or "").strip()
    except Exception:
        raise AssertionError(f"expect-text failed: element {selector} not found")
    if expected not in text:
        raise AssertionError(f"expect-text failed on {selector}: expected '{expected}' in '{text}'")
    return True


def assert_visible(page, selector: str) -> bool:
    """Verify element is visible. Raises AssertionError if hidden or missing."""
    try:
        el = page.wait_for_selector(selector, timeout=5000, state="visible")
    except Exception:
        raise AssertionError(f"expect-visible failed: {selector} not visible")
    if el is None:
        raise AssertionError(f"expect-visible failed: {selector} not found")
    return True


def assert_url(page, expected: str) -> bool:
    """Verify page URL contains expected string. Raises AssertionError on mismatch."""
    actual = page.url
    if expected not in actual:
        raise AssertionError(f"expect-url failed: expected '{expected}' in '{actual}'")
    return True


# ── Phase 5: Test Report ──────────────────────────────────────────

class AssertionReport:
    """Accumulates assertion results, produces pass/fail summary."""

    def __init__(self):
        self.results: list[dict] = []

    @property
    def passed(self) -> int:
        return sum(1 for r in self.results if r["status"] == "PASS")

    @property
    def failed(self) -> int:
        return sum(1 for r in self.results if r["status"] == "FAIL")

    def total(self) -> int:
        return len(self.results)

    def record(self, assertion_type: str, selector: str, value: str, ok: bool, error: str = ""):
        self.results.append({
            "assertion": assertion_type,
            "selector": selector,
            "value": value,
            "status": "PASS" if ok else "FAIL",
            "error": error,
        })

    def summary(self) -> dict:
        return {"total": self.total(), "passed": self.passed, "failed": self.failed}

    def to_json(self) -> str:
        return json.dumps(
            {**self.summary(), "results": self.results}, indent=2
        )

    def to_text(self) -> str:
        lines = [f"{self.passed} passed, {self.failed} failed ({self.total()} total)"]
        for r in self.results:
            status = "✅" if r["status"] == "PASS" else "❌"
            line = f"  {status} {r['assertion']} | {r['selector']} | {r['value']}"
            if r["error"]:
                line += f" — {r['error']}"
            lines.append(line)
        return "\n".join(lines)


def run_assertions(page, specs: list[dict]) -> AssertionReport:
    """Batch assertion runner. Each spec: {type, selector, value}.

    Returns AssertionReport with accumulated results.
    """
    report = AssertionReport()
    dispatch = {
        "expect-text": lambda s: (assert_text(page, s["selector"], s["value"]), s["selector"], s["value"]),
        "expect-visible": lambda s: (assert_visible(page, s["selector"]), s["selector"], "visible"),
        "expect-url": lambda s: (assert_url(page, s["value"]), "url", s["value"]),
    }
    for spec in specs:
        atype = spec["type"]
        try:
            fn = dispatch[atype]
            fn(spec)  # raises on fail
            report.record(atype, spec.get("selector", ""), spec.get("value", ""), True)
        except (AssertionError, KeyError) as e:
            report.record(atype, spec.get("selector", ""), spec.get("value", ""), False, str(e))
    return report


def action_report(page, args):
    """CLI: run batch assertions, output report (JSON or text)."""
    try:
        specs = json.loads(args.value)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON for report specs: {e}")
    report = run_assertions(page, specs)
    if args.output and args.output.lower().endswith(".json"):
        print(report.to_json())
    else:
        print(report.to_text())


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


# ── Phase 4: PDF Generation ──────────────────────────────

def generate_pdf(
    page,
    out_path: str,
    *,
    format: str | None = None,
    print_background: bool = False,
    margin: dict | None = None,
    page_range: dict | None = None,
    scale: float = 1.0,
) -> str:
    """Generate PDF from current page.

    Args:
        page: Playwright page.
        out_path: Output file path (auto-appends .pdf if missing).
        format: Paper format (A4, Letter, Legal, etc.).
        print_background: Include background graphics.
        margin: Dict with top, right, bottom, left (e.g. {"top": "1cm"}).
        page_range: Dict with from/to (1-based) page numbers.
        scale: Scale factor (0.1–2.0).

    Returns:
        Path to generated PDF file.
    """
    # Auto-append .pdf extension
    if not out_path.lower().endswith(".pdf"):
        out_path = out_path + ".pdf"

    opts = {}
    if format:
        opts["format"] = format
    if print_background:
        opts["print_background"] = True
    if margin:
        opts["margin"] = margin
    if page_range:
        f = page_range.get("from", 0) + 1  # 0→1-based
        t = page_range.get("to", 0) + 1
        opts["page_ranges"] = f"{f}-{t}"
    if scale != 1.0:
        opts["scale"] = scale

    page.pdf(path=out_path, **opts)
    return out_path


def action_pdf(page, args):
    """CLI action: generate PDF from current page."""
    output = args.output or "output.pdf"
    result = generate_pdf(page, output)
    print(f"[pdf] Generated: {result}")


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


def action_assert_text(page, args):
    """CLI: expect-text."""
    assert_text(page, args.selector, args.value)
    print(f"[assert] expect-text passed: {args.selector} contains '{args.value}'")


def action_assert_visible(page, args):
    """CLI: expect-visible."""
    assert_visible(page, args.selector)
    print(f"[assert] expect-visible passed: {args.selector}")


def action_assert_url(page, args):
    """CLI: expect-url."""
    expected = args.value or args.url
    assert_url(page, expected)
    print(f"[assert] expect-url passed: contains '{expected}'")


# ── Phase 6: iframe Context Switching ────────────────────────────────


def iframe_list(page) -> list[dict]:
    """List all iframes on page with metadata."""
    return page.evaluate("""
        () => {
            const frames = document.querySelectorAll('iframe');
            return Array.from(frames).map(f => ({
                name: f.id || f.name || '',
                src: f.src || f.getAttribute('srcdoc') ? 'inline' : '',
                visible: f.offsetParent !== null,
                width: f.offsetWidth,
                height: f.offsetHeight,
            }));
        }
    """)


def _frame_locator(page, iframe_selector: str):
    """Get FrameLocator for iframe by CSS selector."""
    fl = page.frame_locator(iframe_selector)
    return fl


def iframe_query(page, iframe_selector: str | None, inner_selector: str) -> str | None:
    """One-liner: read text content from element inside iframe.

    Args:
        page: Playwright page.
        iframe_selector: CSS selector for iframe, or None for main frame.
        inner_selector: CSS selector inside the iframe.
    """
    if iframe_selector is None:
        try:
            return page.locator(inner_selector).inner_text(timeout=5000)
        except Exception:
            return None

    fl = _frame_locator(page, iframe_selector)
    try:
        return fl.locator(inner_selector).inner_text(timeout=5000)
    except Exception:
        return None


def iframe_click(page, iframe_selector: str, inner_selector: str) -> None:
    """Click element inside iframe."""
    fl = _frame_locator(page, iframe_selector)
    fl.locator(inner_selector).click(timeout=5000)


def iframe_fill(page, iframe_selector: str, inner_selector: str, text: str) -> None:
    """Fill input inside iframe."""
    fl = _frame_locator(page, iframe_selector)
    fl.locator(inner_selector).fill(text, timeout=5000)


def iframe_enter(page, iframe_selector: str) -> None:
    """Enter iframe context for subsequent operations.
    Stores frame_locator reference on page for chained ops.
    """
    fl = _frame_locator(page, iframe_selector)
    page._active_fl = fl  # type: ignore[attr-defined]


def iframe_exit(page) -> None:
    """Exit iframe context, return to main frame."""
    page._active_fl = None  # type: ignore[attr-defined]


def iframe_extract(page, iframe_selector: str, inner_selector: str) -> str:
    """Extract text from single element inside iframe."""
    fl = _frame_locator(page, iframe_selector)
    try:
        return fl.locator(inner_selector).inner_text(timeout=5000)
    except Exception:
        return ""


def iframe_multi_extract(page, iframe_selector: str, selector: str) -> list[str]:
    """Extract text from multiple elements inside iframe."""
    fl = _frame_locator(page, iframe_selector)
    return fl.locator(selector).all_inner_texts()


def action_iframe(page, args):
    """CLI action: iframe operations."""
    action_type = args.action

    if action_type == "iframe-list":
        frames = iframe_list(page)
        print(json.dumps(frames, indent=2))

    elif action_type == "iframe-query":
        if not args.selector or not args.value:
            raise ValueError("iframe-query: --selector (iframe) and --value (inner) required")
        result = iframe_query(page, args.selector, args.value)
        if result:
            print(result)

    elif action_type == "iframe-click":
        if not args.selector or not args.value:
            raise ValueError("iframe-click: --selector (iframe) and --value (inner) required")
        iframe_click(page, args.selector, args.value)
        print(f"[iframe] Clicked: {args.selector} → {args.value}")

    elif action_type == "iframe-fill":
        if not args.selector or not args.value:
            raise ValueError("iframe-fill: --selector (iframe), --value (inner) and --output (text) required")
        text = args.output or ""
        iframe_fill(page, args.selector, args.value, text)
        print(f"[iframe] Filled: {args.selector} → {args.value} = {text}")

    elif action_type == "iframe-extract":
        if not args.selector or not args.value:
            raise ValueError("iframe-extract: --selector (iframe) and --value (inner) required")
        result = iframe_extract(page, args.selector, args.value)
        print(result)

    else:
        raise ValueError(f"Unknown iframe action: {action_type}")


# ── Phase 6: Shadow DOM Piercing ──────────────────────────────────


def shadow_query(page, host_selector: str, inner_selector: str) -> str | None:
    """Query text content from element inside shadow DOM."""
    result = page.evaluate("""
        (params) => {
            const host = document.querySelector(params.hostSel);
            if (!host) return null;
            const shadow = host.shadowRoot;
            if (!shadow) return null;
            const el = shadow.querySelector(params.innerSel);
            return el ? el.textContent.trim() : null;
        }
    """, {"hostSel": host_selector, "innerSel": inner_selector})
    return result


def shadow_click(page, host_selector: str, inner_selector: str) -> None:
    """Click element inside shadow DOM."""
    page.evaluate("""
        (params) => {
            const host = document.querySelector(params.hostSel);
            if (!host) throw new Error('Shadow host not found: ' + params.hostSel);
            const shadow = host.shadowRoot;
            if (!shadow) throw new Error('No shadow root on: ' + params.hostSel);
            const el = shadow.querySelector(params.innerSel);
            if (!el) throw new Error('Inner element not found: ' + params.innerSel);
            el.click();
        }
    """, {"hostSel": host_selector, "innerSel": inner_selector})


def shadow_fill(page, host_selector: str, inner_selector: str, text: str) -> None:
    """Fill input/textarea inside shadow DOM."""
    page.evaluate("""
        (params) => {
            const host = document.querySelector(params.hostSel);
            if (!host) throw new Error('Shadow host not found: ' + params.hostSel);
            const shadow = host.shadowRoot;
            if (!shadow) throw new Error('No shadow root on: ' + params.hostSel);
            const el = shadow.querySelector(params.innerSel);
            if (!el) throw new Error('Inner element not found: ' + params.innerSel);
            el.value = params.text;
            el.dispatchEvent(new Event('input', {bubbles: true}));
            el.dispatchEvent(new Event('change', {bubbles: true}));
        }
    """, {"hostSel": host_selector, "innerSel": inner_selector, "text": text})


def shadow_extract_all(page, host_selector: str, inner_selector: str) -> list[str]:
    """Extract text from matching inner elements across multiple shadow hosts."""
    return page.evaluate("""
        (params) => {
            const hosts = document.querySelectorAll(params.hostSel);
            const results = [];
            for (const host of hosts) {
                const shadow = host.shadowRoot;
                if (!shadow) continue;
                const el = shadow.querySelector(params.innerSel);
                if (el) results.push(el.textContent.trim());
            }
            return results;
        }
    """, {"hostSel": host_selector, "innerSel": inner_selector})


def shadow_pierce(page, chain: str) -> str | None:
    """Pierce multiple shadow DOM levels via chained selector.

    Syntax: '#host >> .level1 >> .deep-text'
    Each segment after first is queried inside previous element's shadowRoot.
    """
    parts = [p.strip() for p in chain.split(">>")]
    if not parts:
        raise ValueError("shadow-pierce: empty selector chain")

    try:
        result = page.evaluate("""
            (selectors) => {
                let el = document.querySelector(selectors[0]);
                if (!el) return null;
                for (let i = 1; i < selectors.length; i++) {
                    const shadow = el.shadowRoot;
                    if (!shadow) {
                        throw new Error('No shadow root at segment ' + i + ': ' + selectors[i-1]);
                    }
                    el = shadow.querySelector(selectors[i]);
                    if (!el) {
                        throw new Error('Element not found at segment ' + i + ': ' + selectors[i]);
                    }
                }
                return el.textContent.trim();
            }
        """, parts)
    except Exception as e:
        raise ValueError(str(e))
    return result


def shadow_detect(page) -> list[dict]:
    """Find all shadow hosts on the page."""
    return page.evaluate("""
        () => {
            const all = document.querySelectorAll('*');
            return Array.from(all)
                .filter(el => el.shadowRoot)
                .map(el => ({
                    tag: el.tagName.toLowerCase(),
                    id: el.id || '',
                    classList: Array.from(el.classList || []),
                    childCount: (el.shadowRoot && el.shadowRoot.children.length) || 0
                }));
        }
    """)


def action_shadow(page, args):
    """CLI action: shadow DOM operations."""
    action_type = args.action

    if action_type == "shadow-detect":
        hosts = shadow_detect(page)
        print(json.dumps(hosts, indent=2))

    elif action_type == "shadow-query":
        if not args.selector or not args.value:
            raise ValueError("shadow-query: --selector (host) and --value (inner) required")
        result = shadow_query(page, args.selector, args.value)
        if result:
            print(result)

    elif action_type == "shadow-click":
        if not args.selector or not args.value:
            raise ValueError("shadow-click: --selector (host) and --value (inner) required")
        shadow_click(page, args.selector, args.value)
        print(f"[shadow] Clicked: {args.selector} >> {args.value}")

    elif action_type == "shadow-fill":
        if not args.selector or not args.value:
            raise ValueError("shadow-fill: --selector (host) and --value (inner) required")
        text = args.output or ""
        shadow_fill(page, args.selector, args.value, text)
        print(f"[shadow] Filled: {args.selector} >> {args.value}")

    elif action_type == "shadow-extract":
        if not args.selector or not args.value:
            raise ValueError("shadow-extract: --selector (host) and --value (inner) required")
        results = shadow_extract_all(page, args.selector, args.value)
        print(json.dumps(results, indent=2))

    elif action_type == "shadow-pierce":
        if not args.value:
            raise ValueError("shadow-pierce: --value (chain) required")
        result = shadow_pierce(page, args.value)
        if result:
            print(result)

    else:
        raise ValueError(f"Unknown shadow action: {action_type}")


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
    "pdf": action_pdf,
    "expect-text": action_assert_text,
    "expect-visible": action_assert_visible,
    "expect-url": action_assert_url,
    "screenshot-diff": action_screenshot_diff,
    "report": action_report,
    "shadow-query": action_shadow,
    "shadow-click": action_shadow,
    "shadow-fill": action_shadow,
    "shadow-extract": action_shadow,
    "shadow-pierce": action_shadow,
    "shadow-detect": action_shadow,
    "iframe-list": action_iframe,
    "iframe-query": action_iframe,
    "iframe-click": action_iframe,
    "iframe-fill": action_iframe,
    "iframe-extract": action_iframe,
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
    parser.add_argument("--baseline", help="Baseline screenshot for diff comparison")
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
