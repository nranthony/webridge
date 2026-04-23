"""HTML → markdown helpers (thin wrappers around trafilatura / markdownify)."""

from __future__ import annotations

from typing import Optional


def html_to_markdown(html: str, *, url: Optional[str] = None) -> str:
    """Convert HTML to markdown. Uses trafilatura for article-style pages,
    falls back to markdownify for anything trafilatura can't handle."""
    import trafilatura

    result = trafilatura.extract(html, url=url, output_format="markdown", include_links=True, include_tables=True)
    if result:
        return result

    from markdownify import markdownify as _md

    return _md(html)
