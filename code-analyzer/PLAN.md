# Implementation Roadmap: Code Insight Phase

## Phase 1: Core Scaffolding ✅ Done
- [x] Establish `code-analyst/` directory structure.
- [x] Implement `main.py` with dynamic plugin discovery and loading.
- [x] Define the `BaseAnalyzer` abstract class in `base.py`.

## Phase 2: Analyzer Development ✅ Done
- [x] Build the `RegexAnalyzer` for baseline multi-language support.
- [x] Develop the `PythonASTAnalyzer` for high-fidelity Python mapping.
- [x] Create a `ProjectDetector` utility to automate plugin selection.

## Phase 3: Refinement & Integration (Current)
- [ ] Standardize the JSON output for downstream E2E scenario generators.
- [ ] Implement token-optimization logic to condense analysis results for LLM context windows.
- [ ] Integrate with the `pi-mono` local skill registry.

## Phase 4: Automation & CI
- [ ] Setup automated "Commit and Push" triggers for the agent upon task completion.
- [x] Add unit tests for each analyzer plugin.
