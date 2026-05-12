# Playwright Skill — Implementation Plan

## Phase 1: Core CLI ✅ Done
- [x] Create skill scaffold (`SKILL.md`, `main.py`, `requirements.txt`)
- [x] 8 base actions: navigate, click, type, extract, screenshot, wait, eval, scroll
- [x] Headless Chromium support via `playwright` Python API

## Phase 2: Session Mode
- [x] SQLite-backed state (`.sessions/state.db`)
- [x] Persistent browser context across multiple invocations (storage_state JSON)
- [x] Schema: `sessions` table — url, title, cookies (JSON), updated_at
- [x] Session lifecycle: `start`, `interact`, `stop`
- [x] Auto-recovery on page crash / navigation timeout

## Phase 3: Form Automation
- [x] Auto-detect form fields (input, textarea, select)
- [x] Smart fill — map field names to values from JSON input
- [x] Submit handling — detect form submission + wait for response
- [x] Multi-step form support (wizard flows)

## Phase 4: Data Extraction
- [x] Structured scraping — table rows → JSON/CSV
- [x] Repeatable selectors — nth-child, recursive extraction
- [x] Network interception — capture API responses, headers
- [x] PDF generation from page

## Phase 5: Assertions & Testing
- [x] Built-in assertions: `expect-text`, `expect-visible`, `expect-url`
- [x] Wait-for-conditions: network idle, element state, HTTP status
- [x] Screenshot diffing — visual regression detection
- [x] Test report output (passed/failed summary)

## Phase 6: Advanced Patterns
- [x] Shadow DOM piercing
- [x] iframe context switching
- [x] Dialog/alert interception
- [x] File upload automation
- [x] Auth flows — cookie injection, localStorage seeding
- [x] Parallel pages — multi-tab orchestration

## Phase 7: Integration
- [x] Register in pi-mono skill registry (~/.pi/skills/ + ~/.pi/agent/skills/)
- [x] Add unit tests for CLI actions
- [x] Add e2e smoke test (navigate → click → extract → screenshot)
- [x] Document in skill catalog (SKILL.md frontmatter + sections)

## Phase 8: Documentation & Polish
- [ ] SKILL.md — document all 46 actions (currently 8 of 46)
- [ ] SKILL.md — fix session syntax (`session-start` not `--session start`)
- [ ] SKILL.md — bump version to 0.7.0, add missing flags (--retries, --baseline, --nth)
- [ ] Create README.md
- [ ] Sync ~/.pi/skills/playwright/SKILL.md
