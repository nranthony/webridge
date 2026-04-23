"""Static fetch path — ``httpx`` for transport, ``trafilatura`` for extraction."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import httpx

from webridge._logging import get_logger

logger = get_logger(__name__)


@dataclass(slots=True)
class StaticFetchResult:
    url: str
    final_url: str
    status: int
    content_type: Optional[str]
    html: str
    markdown: str
    title: Optional[str]


def _extract(html: str, url: str) -> tuple[str, Optional[str]]:
    """Return ``(markdown, title)``. Falls back to empty string if trafilatura can't extract."""
    import trafilatura  # local import keeps cold-start cheap for callers who don't need it

    markdown = trafilatura.extract(
        html,
        url=url,
        output_format="markdown",
        include_links=True,
        include_tables=True,
        favor_recall=False,
    )
    if markdown is None:
        # Try a looser pass before giving up.
        markdown = trafilatura.extract(
            html,
            url=url,
            output_format="markdown",
            include_links=True,
            include_tables=True,
            favor_recall=True,
            no_fallback=False,
        )

    title: Optional[str] = None
    try:
        meta = trafilatura.extract_metadata(html, default_url=url)
        if meta is not None:
            title = meta.title
    except Exception as exc:  # metadata extraction is best-effort
        logger.debug("metadata extract failed for {}: {}", url, exc)

    return (markdown or ""), title


def fetch_static(
    url: str,
    *,
    user_agent: str,
    timeout: float = 30.0,
    follow_redirects: bool = True,
) -> StaticFetchResult:
    """Fetch ``url`` with httpx and extract main content with trafilatura.

    Raises ``httpx.HTTPError`` on transport failure; callers decide whether
    to fall back to the dynamic path.
    """
    headers = {"User-Agent": user_agent}
    logger.info("static fetch {}", url)
    with httpx.Client(timeout=timeout, follow_redirects=follow_redirects, headers=headers) as client:
        response = client.get(url)
        response.raise_for_status()
        html = response.text
        final_url = str(response.url)
        status = response.status_code
        content_type = response.headers.get("content-type")

    markdown, title = _extract(html, final_url)
    return StaticFetchResult(
        url=url,
        final_url=final_url,
        status=status,
        content_type=content_type,
        html=html,
        markdown=markdown,
        title=title,
    )
