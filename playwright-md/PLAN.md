# playwright-md Skill — Implementation Plan

## Goal
Single CLI skill chaining Playwright (browser) + html2md (converter) → URL → Markdown output. Eliminates manual 2-step piping.

---

## Phase 1: Core Scaffold ✅
- [x] Create `playwright-md/` directory
- [x] Write `SKILL.md`, `STRUCTURE.md`, `AGENTS.md`, `PLAN.md`
- [x] Implement `main.py` CLI entry point (argparse dispatcher)
- [x] Define `--url`, `--action page-to-md` as primary interface
- [x] Resolve sibling skill paths: `../playwright/`, `../html2md/`

## Phase 2: Unified `page-to-md` Action ✅
- [x] Navigate URL via Playwright → `domcontentloaded`
- [x] Extract `document.documentElement.outerHTML`
- [x] Pipe raw HTML → html2md conversion pipeline
- [x] Markdown to stdout, errors to stderr, exit 1 on failure

## Phase 3: Wait & Retry Logic ✅
- [x] `--wait-for <selector>` — wait for selector before extraction
- [x] `--wait-for-url <pattern>` — wait for URL match
- [x] `--timeout <MS>` — navigation timeout (default 30000)
- [x] `--retries <N>` — auto-retry on crash/timeout

## Phase 4: Auth & Session Support ✅
- [x] `--cookies <JSON>` — inject cookies before navigate
- [x] `--headers <JSON>` — inject custom headers
- [x] `--session-dir <path>` — persistent storage state (reuses playwright session mode)

## Phase 5: Advanced Extraction ✅
- [x] `--selector <CSS>` — extract sub-region HTML instead of full page
- [x] `--strip-scripts` — remove `<script>` tags pre-conversion (default: true, hardcoded in sanitize_html)
- [x] `--strip-styles` — remove `<style>` tags pre-conversion (default: true, hardcoded in sanitize_html)
- [x] `--backend <markdownify|html2text>` — choose html2md backend

## Phase 6: Multi-Page & Batch ✅
- [x] `--urls <file>` — batch process URL list → one Markdown per URL
- [x] `--output-dir <dir>` — write output to directory
- [x] `--output <file>` — single file output

## Phase 7: Testing & Integration ✅
- [x] Unit tests (mock Playwright, verify HTML→MD pipeline) — 30 tests passing
- [x] E2E smoke test: navigate → extract → convert → assert Markdown (pipeline-level, no browser)
- [x] Register in `.pi/skills/playwright-md/`
- [x] Verify agent invocation via terminal

## Phase 8: Documentation & Polish ✅
- [x] Finalize SKILL.md (all actions + examples, v0.2.0)
- [x] README.md
- [x] Sync `~/.pi/skills/playwright-md/SKILL.md`
