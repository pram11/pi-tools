"""Post-processor — clean up Markdown output."""

import re


def process(md: str) -> str:
    """Clean Markdown: strip trailing spaces, dedup blank lines, trim edges."""
    lines = [line.rstrip() for line in md.splitlines()]
    # collapse 3+ blank lines → 1
    cleaned = re.sub(r"\n{3,}", "\n\n", "\n".join(lines))
    return cleaned.strip()
