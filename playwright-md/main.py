#!/usr/bin/env python3
"""playwright-md: URL → Markdown via Playwright + html2md chain."""

import argparse
import sys
from pathlib import Path

from lib.path_resolver import SkillPathResolver

VERSION = "0.1.0"
SKILL_ROOT = Path(__file__).resolve().parent


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="playwright-md",
        description="URL to Markdown. Chains Playwright (browser) + html2md (converter).",
    )

    parser.add_argument("--version", action="version", version=f"%(prog)s {VERSION}")
    parser.add_argument("--url", type=str, help="Target URL (required for page-to-md)")
    parser.add_argument(
        "--action",
        choices=["page-to-md"],
        default="page-to-md",
        help="Action to perform (default: page-to-md)",
    )
    parser.add_argument("--output", type=str, default=None, help="Write Markdown to file (default: stdout)")
    parser.add_argument("--wait-for", type=str, default=None, help="Wait for CSS selector before extraction")
    parser.add_argument("--wait-for-url", type=str, default=None, help="Wait for URL to match substring")
    parser.add_argument("--timeout", type=int, default=30000, help="Navigation timeout in ms (default: 30000)")
    parser.add_argument("--retries", type=int, default=1, help="Auto-retry on crash/timeout (default: 1)")
    parser.add_argument("--selector", type=str, default=None, help="CSS selector for sub-region extraction")
    parser.add_argument(
        "--backend",
        choices=["markdownify", "html2text"],
        default="markdownify",
        help="html2md converter backend (default: markdownify)",
    )
    parser.add_argument("--cookies", type=str, default=None, help='JSON cookies array [{"name":"x","value":"y"}]')
    parser.add_argument("--headers", type=str, default=None, help='JSON headers {"User-Agent":"bot"}')
    parser.add_argument(
        "--session-dir", type=str, default=str(SKILL_ROOT / ".sessions"), help="Persistent browser state dir"
    )
    parser.add_argument("--urls", type=str, default=None, help="File with one URL per line (batch mode)")
    parser.add_argument("--output-dir", type=str, default=None, help="Output directory for batch mode")

    return parser


def validate_args(args: argparse.Namespace) -> list[str]:
    """Validate parsed args. Return list of error messages (empty = valid)."""
    errors = []
    if args.urls:
        if not Path(args.urls).exists():
            errors.append(f"Error: URL file not found: {args.urls}")
    elif args.action == "page-to-md" and not args.url:
        errors.append("Error: --url is required for action 'page-to-md'")
    return errors


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    errors = validate_args(args)
    if errors:
        for err in errors:
            print(err, file=sys.stderr)
        return 1

    # Resolve sibling skill paths
    resolver = SkillPathResolver(SKILL_ROOT)
    sys.path.insert(0, str(resolver.html2md_path))

    if args.urls:
        # Batch mode
        try:
            from lib.batch import run_batch
        except ImportError:
            print("Error: batch module not available.", file=sys.stderr)
            return 1

        return run_batch(
            url_file=args.urls,
            output_dir=args.output_dir,
            wait_for=args.wait_for,
            wait_for_url=args.wait_for_url,
            timeout=args.timeout,
            retries=args.retries,
            selector=args.selector,
            backend=args.backend,
            cookies=args.cookies,
            headers=args.headers,
            session_dir=args.session_dir,
        )

    if args.action == "page-to-md":
        try:
            from lib.orchestrator import run_page_to_md
        except ImportError:
            print("Error: orchestrator not available. Implement Phase 2 first.", file=sys.stderr)
            return 1

        return run_page_to_md(
            url=args.url,
            output=args.output,
            wait_for=args.wait_for,
            wait_for_url=args.wait_for_url,
            timeout=args.timeout,
            retries=args.retries,
            selector=args.selector,
            backend=args.backend,
            cookies=args.cookies,
            headers=args.headers,
            session_dir=args.session_dir,
        )

    return 0


if __name__ == "__main__":
    sys.exit(main())
