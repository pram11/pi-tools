# Implementation Roadmap: Code Insight Phase

## Phase 1: Core Scaffolding ✅ Done
- [x] Establish `code-analyzer/` directory structure.
- [x] Implement `main.py` with dynamic plugin discovery and loading.
- [x] Define the `BaseAnalyzer` abstract class in `base.py`.

## Phase 2: Analyzer Development ✅ Done
- [x] Build the `RegexAnalyzer` for baseline multi-language support.
- [x] Develop the `PythonASTAnalyzer` for high-fidelity Python mapping.
- [x] Create a `ProjectDetector` utility to automate plugin selection.

## Phase 3: Refinement & Integration (Current)
- [x] Standardize the JSON output for downstream E2E scenario generators.
- [x] Implement token-optimization logic to condense analysis results for LLM context windows.
- [x] Integrate with the `pi-mono` local skill registry.

## Phase 4: Automation & CI
- [x] Setup automated "Commit and Push" triggers for the agent upon task completion.
- [x] Add unit tests for each analyzer plugin.

## Phase 5: JS/TSX Deep Analysis (From Shallow Scan Gaps)

### Context
Shallow scan of portfolio site → 13 files mapped, but only surface-level. RegexAnalyzer returned 0 identifiers, 0 complexity metrics.

### Required Features
- [x] **JSXASTAnalyzer** — new plugin using `tree-sitter` or `babel-parser` (via `py-tree-sitter-javascript`) to parse `.tsx`/`.jsx` ASTs
- [x] **Identifier Extraction** — extract component names, hooks, imports, exports, props interfaces from JS/TSX files
- [x] **Complexity Metrics** — implement cyclomatic complexity, LOC, nesting depth for JS/TSX (parity with PythonASTAnalyzer)
- [x] **Route Discovery** — parse Next.js `app/` router patterns (`page.tsx`, `layout.tsx`, dynamic `[slug].tsx`) automatically
- [x] **Cross-File Edges** — map import/export relationships between components (e.g., `Navbar` imports `Link` from `next/navigation`)
- [x] **Formal .tsx/.jsx Support** — promote patched file-extension support to first-class language detection in `ProjectDetector`
- [x] **Output Schema Extension** — add `identifiers`, `complexity`, `edges` fields to JSON output for JS/TSX (match Python schema)
- [ ] **Benchmark** — validate against Depwire's 44-symbol extraction on same portfolio site
