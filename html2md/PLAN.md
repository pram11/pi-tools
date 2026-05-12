# Implementation Plan: html2md Skill

## Phase 1: Core Scaffolding ✅
- [x] Establish `html2md/` directory structure.
- [x] Implement `main.py` CLI entry point (argparse dispatcher).
- [x] Define `BaseConverter` abstract class in `base.py`.
- [x] Write `SKILL.md`, `AGENTS.md`, `PLAN.md`.

## Phase 2: Conversion Pipeline ✅
- [x] Implement `lib/html_parser.py` — HTML sanitization + BeautifulSoup tree construction.
- [x] Implement `lib/md_converter.py` — core conversion engine with strategy pattern.
- [x] Implement `plugins/markdownify_backend.py` — primary converter (markdownify lib).
- [x] Implement `plugins/html2text_backend.py` — fallback converter (html2text lib).

## Phase 3: Post-Processing & Output ✅
- [x] Implement `lib/post_processor.py` — cleanup: dedup blanks, strip trailing spaces, normalize lists.
- [x] Support `--output <file>` flag for file destination.
- [x] Support `--wrap <N>` for line wrapping.

## Phase 4: Input Modes ✅
- [x] `--file <path>` — local HTML file input.
- [x] `--html "<string>"` — inline HTML string input.
- [x] stdin pipe — `echo "<h1>hi</h1>" | python main.py`.

## Phase 5: Testing & Integration
- [ ] Unit tests for each backend (markdownify, html2text).
- [ ] End-to-end tests: raw HTML → expected Markdown output.
- [ ] Register in `.pi/skills/html2md/` skill directory.
- [ ] Verify agent can invoke skill via terminal commands.

## Future (Out of Scope — Chained Skills)
- [ ] URL mode via Playwright skill → pipe `page.content()` into html2md.
