"""Dynamic fetch path — Crawl4AI (Playwright under the hood).

Ported from ``wearable_data_testing/scripts/fetch_url.py`` — the minimum
viable JS-aware fetcher. Pulls Crawl4AI only when called; the base
install must stay lightweight.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Optional

from webridge._logging import get_logger

logger = get_logger(__name__)


class DynamicFetchError(RuntimeError):
    """Raised when Crawl4AI or its Playwright browser is unusable."""


@dataclass(slots=True)
class DynamicFetchResult:
    url: str
    final_url: str
    status: int
    content_type: Optional[str]
    html: Optional[str]
    markdown: str
    title: Optional[str]


async def _crawl(url: str) -> DynamicFetchResult:
    try:
        from crawl4ai import AsyncWebCrawler  # type: ignore[import-not-found]
    except ImportError as exc:
        raise DynamicFetchError(
            "crawl4ai is not installed. Install the 'dynamic' extra: "
            'uv pip install -e ".[dynamic]" && playwright install chromium'
        ) from exc

    try:
        async with AsyncWebCrawler() as crawler:
            result = await crawler.arun(url=url)
    except Exception as exc:  # Playwright binary missing, launch failure, etc.
        msg = str(exc).lower()
        if "playwright" in msg or "executable" in msg or "chromium" in msg:
            raise DynamicFetchError(
                "Playwright browser missing. Run: playwright install chromium"
            ) from exc
        raise DynamicFetchError(f"crawl4ai failed for {url}: {exc}") from exc

    markdown = (getattr(result, "markdown", None) or "").strip()
    html = getattr(result, "cleaned_html", None) or getattr(result, "html", None)
    status = int(getattr(result, "status_code", 0) or 200)
    final_url = getattr(result, "url", None) or url
    title = None
    metadata = getattr(result, "metadata", None)
    if isinstance(metadata, dict):
        title = metadata.get("title")

    return DynamicFetchResult(
        url=url,
        final_url=final_url,
        status=status,
        content_type=None,
        html=html,
        markdown=markdown,
        title=title,
    )


def fetch_dynamic(url: str) -> DynamicFetchResult:
    """Synchronous wrapper around the async Crawl4AI call."""
    logger.info("dynamic fetch {}", url)
    return asyncio.run(_crawl(url))
