"""Tavily backend — stub. Implement when a real consumer needs it."""

from __future__ import annotations

from webridge.models.search import SearchResult


def search_tavily(query: str, *, limit: int, api_key: str) -> list[SearchResult]:
    raise NotImplementedError("Tavily backend not yet implemented (v0.1 stub)")
