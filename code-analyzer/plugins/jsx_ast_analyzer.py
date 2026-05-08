"""JSXASTAnalyzer – tree-sitter-based TSX/JSX source mapping."""

import re
from pathlib import Path
from typing import Any

from tree_sitter import Language, Parser

import tree_sitter_typescript as tst

from base import BaseAnalyzer

_TSX_LANGUAGE = Language(tst.language_tsx())

# Next.js app/ router file patterns
_ROUTE_FILES = {"page.tsx", "layout.tsx", "loading.tsx", "error.tsx", "not-found.tsx", "route.ts"}
_DYNAMIC_RE = re.compile(r"^\[(.+)\]\.tsx$")


def _is_route_file(path: Path, base: Path) -> bool:
    """Check if file is a Next.js app/ router entry point.
    Handles both app/ and src/app/ layouts."""
    for sub in ("app", "src/app"):
        try:
            rel = path.relative_to(base / sub)
        except ValueError:
            continue
        if rel.name in _ROUTE_FILES:
            return True
    return False


def _get_route_path(path: Path, base: Path) -> str | None:
    """Convert file path to Next.js route URL."""
    for sub in ("app", "src/app"):
        try:
            rel = path.relative_to(base / sub)
        except ValueError:
            continue
        if rel.name in _ROUTE_FILES:
            route_parts = []
            for part in rel.parts:
                if part in _ROUTE_FILES:
                    continue
                route_parts.append(part)
            route = "/".join(route_parts)
            return f"/{route}" if route else "/"
    return None


def _extract_imports(node) -> list[tuple[str, str]]:
    """Extract (imported_name, source_module) from import_statement nodes."""
    imports = []
    for child in node.children:
        if child.type != "import_statement":
            continue
        source = _get_string_value(child, "string")
        if not source:
            continue
        for gc in child.children:
            if gc.type == "import_clause":
                for ggc in gc.children:
                    if ggc.type == "identifier":
                        imports.append((ggc.text.decode(), source))
                    elif ggc.type == "named_imports":
                        for s in ggc.children:
                            if s.type == "import_specifier":
                                for gsc in s.children:
                                    if gsc.type == "identifier":
                                        imports.append((gsc.text.decode(), source))
                                        break
                            elif s.type == "namespace_import":
                                for gsc in s.children:
                                    if gsc.type == "identifier":
                                        imports.append((gsc.text.decode(), source))
    return imports


def _get_string_value(node, child_type: str = "string") -> str | None:
    """Extract string content from a string node."""
    for child in node.children:
        if child.type == child_type:
            text = child.text.decode()
            return text.strip('"').strip("'").strip("`")
    return None


def _is_pascal_case(name: str) -> bool:
    return name and len(name) > 0 and name[0].isupper() and not name.startswith("use")


def _is_hook(name: str) -> bool:
    return name.startswith("use") and len(name) > 3 and name[3].isupper()


def _find_identifiers(node, seen: set) -> list[str]:
    """Recursively find all exported/named identifiers from a node tree."""
    results = []

    # function_declaration: function X() {}
    if node.type == "function_declaration":
        for child in node.children:
            if child.type == "identifier":
                name = child.text.decode()
                if name not in seen:
                    seen.add(name)
                    results.append(name)
                break

    # class_declaration: class X {}
    elif node.type == "class_declaration":
        for child in node.children:
            if child.type == "identifier":
                name = child.text.decode()
                if name not in seen:
                    seen.add(name)
                    results.append(name)
                break

    # lexical_declaration: const X = () => {}
    elif node.type == "lexical_declaration":
        for child in node.children:
            if child.type == "variable_declarator":
                for gc in child.children:
                    if gc.type == "identifier":
                        name = gc.text.decode()
                        if (_is_pascal_case(name) or _is_hook(name)) and name not in seen:
                            seen.add(name)
                            results.append(name)
                        break

    # variable_declaration (var/let)
    elif node.type == "variable_declaration":
        for child in node.children:
            if child.type == "variable_declarator":
                for gc in child.children:
                    if gc.type == "identifier":
                        name = gc.text.decode()
                        if (_is_pascal_case(name) or _is_hook(name)) and name not in seen:
                            seen.add(name)
                            results.append(name)
                        break

    # interface_declaration: interface X {}
    elif node.type == "interface_declaration":
        for child in node.children:
            if child.type in ("type_identifier", "identifier"):
                name = child.text.decode()
                if name not in seen:
                    seen.add(name)
                    results.append(name)
                break

    # type_alias_declaration: type X = ...
    elif node.type == "type_alias_declaration":
        for child in node.children:
            if child.type in ("type_identifier", "identifier"):
                name = child.text.decode()
                if name not in seen:
                    seen.add(name)
                    results.append(name)
                break

    return results


def _walk_exports(node, seen: set) -> list[str]:
    """Walk export_statement nodes to find exported names."""
    results = []

    for child in node.children:
        if child.type == "export_statement":
            for gc in child.children:
                results.extend(_find_identifiers(gc, seen))
        else:
            # Top-level declarations (non-exported)
            results.extend(_find_identifiers(child, seen))

    return results


class JSXASTAnalyzer(BaseAnalyzer):
    """Deep structural parsing of .tsx/.jsx files using tree-sitter."""

    @property
    def languages(self) -> list[str]:
        return [".tsx", ".jsx"]

    @staticmethod
    def _count_complexity(node) -> int:
        """Cyclomatic complexity: count branch points."""
        branch_types = {
            "if_statement", "else_clause", "for_statement", "for_in_statement",
            "while_statement", "do_statement", "switch_statement", "case_statement",
            "catch_clause", "conditional_expression",
        }
        score = 0
        for child in node.children:
            if child.type in branch_types:
                score += 1
            elif child.type in ("logical_and_expression", "logical_or_expression"):
                score += 1
            score += JSXASTAnalyzer._count_complexity(child)
        return score

    @staticmethod
    def _count_loc(source: str) -> int:
        return len(source.strip().splitlines())

    @staticmethod
    def _max_nesting(node, depth: int = 0) -> int:
        """Max nesting depth of blocks/JSX."""
        nesting_types = {"statement_block", "jsx_element", "jsx_self_closing_element"}
        max_d = depth
        for child in node.children:
            if child.type in nesting_types:
                child_d = JSXASTAnalyzer._max_nesting(child, depth + 1)
                max_d = max(max_d, child_d)
            else:
                child_d = JSXASTAnalyzer._max_nesting(child, depth)
                max_d = max(max_d, child_d)
        return max_d

    def _analyze_file(self, fpath: Path, base: Path) -> dict[str, Any] | None:
        source = fpath.read_text(encoding="utf-8", errors="replace")
        try:
            tree = _parse(source)
        except Exception:
            return None

        root = tree.root_node
        if not root:
            return None

        seen: set = set()
        identifiers = _walk_exports(root, seen)
        edges = [{"type": "import", "name": n, "source": m} for n, m in _extract_imports(root)]
        route = _get_route_path(fpath, base)
        routes = [route] if route else []

        feature_type = "Logic"
        if routes:
            feature_type = "Route"
        elif any(_is_pascal_case(i) for i in identifiers):
            feature_type = "Component"

        return {
            "file_path": str(fpath),
            "feature_type": feature_type,
            "identifiers": identifiers,
            "complexity_score": JSXASTAnalyzer._count_complexity(root),
            "loc": JSXASTAnalyzer._count_loc(source),
            "nesting_depth": JSXASTAnalyzer._max_nesting(root),
            "routes": routes,
            "edges": edges,
        }

    def analyze(self, target: Path) -> list[dict[str, Any]]:
        results: list[dict[str, Any]] = []
        target_path = target.resolve()

        if target_path.is_file():
            files = [target_path] if target_path.suffix in self.languages else []
        else:
            files = [
                p for p in target_path.rglob("*")
                if p.is_file() and p.suffix in self.languages
            ]

        for f in files:
            try:
                entry = self._analyze_file(f, target_path)
                if entry:
                    results.append(entry)
            except Exception:
                continue

        return results


# Module-level parser instance (reusable)
_parser = Parser(_TSX_LANGUAGE)


def _parse(source: str) -> Any:
    return _parser.parse(bytes(source, "utf-8"))
