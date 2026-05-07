"""Tree-sitter AST-based code chunking (function/class level)."""
from pathlib import Path
from typing import List, Dict

import tree_sitter

LANG_MAP = {
    ".py": ("tree_sitter_python", "python"),
    ".js": ("tree_sitter_javascript", "javascript"),
    ".jsx": ("tree_sitter_javascript", "javascript"),
    ".ts": ("tree_sitter_typescript", "typescript"),
    ".tsx": ("tree_sitter_typescript", "tsx"),
    ".java": ("tree_sitter_java", "java"),
    ".c": ("tree_sitter_c", "c"),
    ".cpp": ("tree_sitter_cpp", "cpp"),
    ".h": ("tree_sitter_c", "c"),
    ".hpp": ("tree_sitter_cpp", "cpp"),
    ".rs": ("tree_sitter_rust", "rust"),
    ".go": ("tree_sitter_go", "go"),
    ".md": (None, "markdown"),
    ".txt": (None, "text"),
}

MAX_CHUNK_SIZE = 4096

# Cache loaded languages
_lang_cache = {}


def _get_parser(lang_key: str):
    """Get or create a tree-sitter Parser for the given language."""
    if lang_key in _lang_cache:
        return _lang_cache[lang_key]

    module_name, lang_name = LANG_MAP.get(lang_key, (None, "text"))
    parser = tree_sitter.Parser()

    if module_name:
        try:
            mod = __import__(module_name)
            lang_fn = getattr(mod, "language")
            lang = lang_fn() if callable(lang_fn) else lang_fn
            parser = tree_sitter.Parser(tree_sitter.Language(lang))
        except Exception as e:
            print(f"[chunker] Warning: Could not load {module_name}: {e}")

    _lang_cache[lang_key] = parser
    return parser


def _detect_lang(file_path: str) -> str:
    ext = Path(file_path).suffix.lower()
    return ext if ext in LANG_MAP else ".py"


def chunk_file(file_path: str) -> List[Dict[str, object]]:
    """Parse file via tree-sitter → yield function/class-level chunks."""
    path = Path(file_path)
    content = path.read_text(encoding="utf-8", errors="replace")
    lang_ext = _detect_lang(str(path))

    chunks: List[Dict[str, object]] = []

    try:
        parser = _get_parser(lang_ext)
        tree = parser.parse(bytes(content, "utf-8"))
        root = tree.root_node
        targets = _collect_definitions(root, lang_ext)

        for node in targets:
            chunk_text = content[node.start_byte:node.end_byte].strip()
            if not chunk_text:
                continue
            chunks.append({
                "index": len(chunks),
                "content": chunk_text,
                "kind": node.type,
                "start_byte": node.start_byte,
            })
    except Exception as e:
        print(f"[chunker] AST parse failed ({e}), falling back to line-based chunking")

    # Fallback: if AST yielded nothing or failed
    if not chunks:
        lines = content.splitlines()
        line_width = max(60, len(content) // max(len(lines), 1))
        for i in range(0, len(lines), MAX_CHUNK_SIZE // max(line_width, 1)):
            block = "\n".join(lines[i:i + (MAX_CHUNK_SIZE // max(line_width, 1))])
            if not block.strip():
                continue
            chunks.append({
                "index": len(chunks),
                "content": block.strip(),
                "kind": "text",
                "start_byte": content.find(block.split("\n")[0]),
            })

    return chunks


# Node types to collect per language
_DEF_TYPES = {
    ".py": {"function_definition", "class_definition"},
    ".js": {"function_declaration", "class_declaration", "method_definition", "arrow_function"},
    ".jsx": {"function_declaration", "class_declaration", "method_definition", "arrow_function"},
    ".ts": {"function_declaration", "class_declaration", "method_definition", "interface_declaration", "type_alias_declaration"},
    ".tsx": {"function_declaration", "class_declaration", "method_definition", "interface_declaration"},
    ".rs": {"function_item", "struct_item", "impl_item"},
    ".go": {"function_declaration"},
}


def _collect_definitions(node, lang_ext: str) -> list:
    """Recursively collect top-level definition nodes."""
    target_types = _DEF_TYPES.get(lang_ext, {"function_definition", "class_definition"})
    result = []

    for child in node.children:
        if child.type in target_types:
            result.append(child)
        # Recurse into bodies to find nested definitions
        elif child.type in {"body", "declaration_list", "field_declaration_list",
                           "statement_list", "block", "associated_type_list"}:
            result.extend(_collect_definitions(child, lang_ext))

    return result
