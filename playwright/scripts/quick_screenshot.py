#!/usr/bin/env python3
"""Quick screenshot utility — single command, no session."""

import sys
from pathlib import Path
from playwright.sync_api import sync_playwright

URL = sys.argv[1] if len(sys.argv) > 1 else "https://example.com"
OUTPUT = sys.argv[2] if len(sys.argv) > 2 else "screenshot.png"

with sync_playwright() as pw:
    page = pw.chromium.launch(headless=True).new_page()
    page.goto(URL, wait_until="domcontentloaded")
    page.screenshot(path=OUTPUT, full_page=True)
    print(f"Saved: {OUTPUT}")
