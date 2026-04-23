"""Top-level fetch entry point with cache-aware static → dynamic fallback."""

from __future__ import annotations

import time
from datetime import datetime, timezone
from typing import Literal, Optional

import httpx

from webridge._config import WebridgeSettings
from webridge._logging import get_logger
from webridge.fetch import dynamic as _dynamic
from webridge.fetch.cache import Cache
from webridge.fetch.dynamic import DynamicFetchError
from webridge.fetch.static import StaticFetchResult, fetch_static
from webridge.models.page import FetchRecord, Page

logger = get_logger(__name__)

FetchMethodArg = Literal["auto", "static", "dynamic"]


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _page_from_static(res: StaticFetchResult, fetched_at: datetime) -> Page:
    return Page(
        url=res.url,
        final_url=res.final_url,
        status=res.status,
        title=res.title,
        markdown=res.markdown,
        html=None,
        fetched_at=fetched_at,
        fetch_method="static",
        content_type=res.content_type,
        char_count=len(res.markdown),
    )


def _page_from_dynamic(res, fetched_at: datetime) -> Page:
    return Page(
        url=res.url,
        final_url=res.final_url,
        status=res.status or 200,
        title=res.title,
        markdown=res.markdown,
        html=None,
        fetched_at=fetched_at,
        fetch_method="dynamic",
        content_type=res.content_type,
        char_count=len(res.markdown),
    )


def _should_fallback(markdown: str, min_chars: int) -> bool:
    return len(markdown.strip()) < min_chars


def fetch(
    url: str,
    *,
    method: FetchMethodArg = "auto",
    refresh: bool = False,
    keep_html: bool = False,
    settings: Optional[WebridgeSettings] = None,
) -> Page:
    """Fetch a URL, returning a :class:`Page`.

    Args:
        url: The URL to fetch.
        method: ``"auto"`` (default) tries static first, falls back to
            dynamic if the result looks empty. ``"static"`` disables the
            fallback; ``"dynamic"`` forces the JS path.
        refresh: If ``True``, ignore any cached copy and refetch.
        keep_html: If ``True``, retain the raw HTML on the returned Page.
        settings: Optional pre-built settings (else read from env).
    """
    cfg = settings or WebridgeSettings()
    cache = Cache(cfg.cache_dir)

    if not refresh:
        cached = cache.get(url)
        if cached is not None:
            return Page(
                url=cached.record.url,
                final_url=cached.record.final_url or cached.record.url,
                status=cached.record.status or 200,
                title=None,
                markdown=cached.markdown,
                html=None,
                fetched_at=cached.record.fetched_at,
                fetch_method=cached.record.fetch_method,
                content_type=None,
                char_count=len(cached.markdown),
            )

    fetched_at = _now()
    started = time.perf_counter()
    error: Optional[str] = None
    page: Optional[Page] = None

    if method in ("auto", "static"):
        try:
            static_res = fetch_static(
                url,
                user_agent=cfg.user_agent,
                timeout=float(cfg.request_timeout),
            )
            page = _page_from_static(static_res, fetched_at)
            if keep_html:
                page = page.model_copy(update={"html": static_res.html})
        except httpx.HTTPError as exc:
            logger.warning("static fetch failed for {}: {}", url, exc)
            error = f"static: {exc}"
            if method == "static":
                raise

        if method == "auto" and page is not None and _should_fallback(page.markdown, cfg.static_min_chars):
            logger.info(
                "static result thin ({} chars < {}); trying dynamic", page.char_count, cfg.static_min_chars
            )
            page = None  # discard and retry dynamically

    if page is None and method in ("auto", "dynamic"):
        try:
            dyn_res = _dynamic.fetch_dynamic(url)
            page = _page_from_dynamic(dyn_res, fetched_at)
            if keep_html and dyn_res.html:
                page = page.model_copy(update={"html": dyn_res.html})
        except DynamicFetchError as exc:
            logger.error("dynamic fetch failed for {}: {}", url, exc)
            if method == "dynamic":
                raise
            # In auto mode, fall through to raise below if we also have no page.
            error = f"{error + '; ' if error else ''}dynamic: {exc}"

    if page is None:
        raise RuntimeError(f"fetch failed for {url}: {error or 'no content'}")

    elapsed_ms = int((time.perf_counter() - started) * 1000)
    record = FetchRecord(
        url=url,
        final_url=page.final_url,
        cache_path=str(cache.path_for(url)),
        fetched_at=fetched_at,
        fetch_method=page.fetch_method,
        elapsed_ms=elapsed_ms,
        from_cache=False,
        status=page.status,
        error=error,
    )
    cache.put(url, page.markdown, record)
    return page


__all__ = ["fetch"]
