#!/usr/bin/env python3
"""html2md — CLI entry point for HTML → Markdown conversion."""

import argparse
import sys

from lib.md_converter import convert, get_converter


def main():
    ap = argparse.ArgumentParser(
        prog="html2md",
        description="Convert HTML to Markdown.",
    )
    ap.add_argument("--file", help="Local HTML file path")
    ap.add_argument("--html", help="Inline HTML string")
    ap.add_argument("--output", help="Write Markdown to file (default: stdout)")
    ap.add_argument(
        "--backend", default="markdownify",
        choices=["markdownify", "html2text"],
        help="Converter backend (default: markdownify)",
    )
    ap.add_argument("--strip-images", action="store_true", help="Omit <img> tags")
    ap.add_argument("--strip-links", action="store_true", help="Omit <a> tags")
    ap.add_argument("--wrap", type=int, default=0, help="Line wrap width (0=no wrap)")

    args = ap.parse_args()

    # --- resolve input ---
    if args.file:
        try:
            html = open(args.file, encoding="utf-8").read()
        except FileNotFoundError:
            print(f"Error: file not found: {args.file}", file=sys.stderr)
            sys.exit(1)
    elif args.html:
        html = args.html
    else:
        if sys.stdin.isatty():
            ap.print_help(sys.stderr)
            sys.exit(1)
        html = sys.stdin.read()
        if not html.strip():
            print("Error: no input provided. Use --file, --html, or pipe via stdin.", file=sys.stderr)
            sys.exit(1)

    # --- convert ---
    try:
        md = convert(html, backend=args.backend)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    # --- wrap ---
    if args.wrap > 0:
        md = _wrap(md, args.wrap)

    # --- output ---
    if args.output:
        open(args.output, "w", encoding="utf-8").write(md + "\n")
        print(f"→ {args.output}", file=sys.stderr)
    else:
        sys.stdout.write(md + "\n")


def _wrap(text: str, width: int) -> str:
    """Simple line-wrap preserving blank lines and Markdown structure."""
    import textwrap
    lines = text.splitlines()
    wrapped = []
    for line in lines:
        if not line.strip():
            wrapped.append("")
        elif line.startswith("#") or line.startswith("-") or line.startswith("|"):
            wrapped.append(line)  # skip headings, lists, tables
        else:
            wrapped.extend(textwrap.wrap(line, width))
    return "\n".join(wrapped)


if __name__ == "__main__":
    main()
