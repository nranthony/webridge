"""DuckDuckGo search via the ``ddgs`` package."""

from __future__ import annotations

from typing import Optional

from webridge._logging import get_logger
from webridge.models.search import SearchResult

logger = get_logger(__name__)


def search_ddgs(query: str, *, limit: int = 10, region: Optional[str] = None) -> list[SearchResult]:
    try:
        from ddgs import DDGS  # type: ignore[import-not-found]
    except ImportError as exc:
        raise ImportError(
            "ddgs is not installed. Install the 'discover' extra: uv pip install -e \".[discover]\""
        ) from exc

    logger.info("ddgs search {!r} (limit={})", query, limit)
    results: list[SearchResult] = []
    with DDGS() as client:
        raw = client.text(query, max_results=limit, region=region) or []
        for i, item in enumerate(raw, start=1):
            url = item.get("href") or item.get("url")
            title = item.get("title") or ""
            snippet = item.get("body") or item.get("snippet")
            if not url or not title:
                continue
            try:
                results.append(
                    SearchResult(url=url, title=title, snippet=snippet, rank=i, backend="ddgs")
                )
            except Exception as exc:
                logger.debug("skipping malformed ddgs result {}: {}", url, exc)
    return results
