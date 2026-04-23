"""Web-search discovery backends."""

from __future__ import annotations

from typing import Optional

from webridge._config import WebridgeSettings
from webridge.models.search import SearchBackend, SearchResult


def search(
    query: str,
    *,
    limit: int = 10,
    backend: SearchBackend = "ddgs",
    region: Optional[str] = None,
    settings: Optional[WebridgeSettings] = None,
) -> list[SearchResult]:
    """Dispatch a search query to the chosen backend.

    Backends are opt-in via extras: ``[discover]`` for ddgs, ``[tavily]``
    for Tavily. ``searxng`` needs no extra, just a reachable instance URL.
    """
    cfg = settings or WebridgeSettings()

    if backend == "ddgs":
        from webridge.discover.ddgs_backend import search_ddgs

        return search_ddgs(query, limit=limit, region=region)
    if backend == "searxng":
        from webridge.discover.searxng_backend import search_searxng

        if not cfg.searxng_url:
            raise ValueError("WEBRIDGE_SEARXNG_URL is required for the searxng backend")
        return search_searxng(query, limit=limit, instance_url=cfg.searxng_url)
    if backend == "tavily":
        from webridge.discover.tavily_backend import search_tavily

        if not cfg.tavily_api_key:
            raise ValueError("WEBRIDGE_TAVILY_API_KEY is required for the tavily backend")
        return search_tavily(query, limit=limit, api_key=cfg.tavily_api_key)

    raise ValueError(f"unknown backend: {backend!r}")


__all__ = ["search"]
