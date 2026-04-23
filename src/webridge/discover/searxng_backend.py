"""SearXNG backend — stub. Implement when a real consumer needs it."""

from __future__ import annotations

from webridge.models.search import SearchResult


def search_searxng(query: str, *, limit: int, instance_url: str) -> list[SearchResult]:
    raise NotImplementedError("SearXNG backend not yet implemented (v0.1 stub)")
