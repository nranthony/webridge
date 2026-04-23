# webridge — Agent API Reference

Compact reference for AI agents writing code that uses `webridge`.
Read alongside `CLAUDE.md` (architecture) and `README.md` (install/config).

---

## Decision guide — which API for which task?

| Task | Use |
|------|-----|
| Fetch a URL → markdown (cache-aware, auto static/dynamic) | `webridge.fetch(url)` |
| Force the JS-rendered path (Crawl4AI / Playwright) | `webridge.fetch(url, method="dynamic")` |
| Disable auto fallback, fail fast if static can't extract | `webridge.fetch(url, method="static")` |
| Bypass cache and refetch | `webridge.fetch(url, refresh=True)` |
| Keep the raw HTML on the returned Page | `webridge.fetch(url, keep_html=True)` |
| Search the web for candidate URLs | `webridge.search("query", limit=5)` |
| Purge cache entries | `webridge.fetch.cache.purge(url=..., older_than=...)` |
| Read-only check where a URL would be cached | `Cache(cfg.cache_dir).path_for(url)` |

---

## Imports

```python
from webridge import fetch, search
from webridge.models import Page, FetchRecord, SearchResult, SearchQuery
from webridge._config import WebridgeSettings
from webridge._logging import get_logger
```

---

## `fetch(url, *, method="auto", refresh=False, keep_html=False, settings=None) -> Page`

Cache-aware top-level entry point.

- `method`: `"auto"` | `"static"` | `"dynamic"`.
  - `"auto"` → static first, fall back to dynamic if extracted markdown < `WEBRIDGE_STATIC_MIN_CHARS` (default 200).
  - `"static"` → static only; raises `httpx.HTTPError` on transport failure.
  - `"dynamic"` → Crawl4AI only; raises `DynamicFetchError` if Playwright is missing.
- `refresh`: bypass and overwrite cached entry.
- `keep_html`: retain raw HTML on the returned `Page` (normally dropped to keep cache small).
- `settings`: inject a pre-built `WebridgeSettings` (useful in tests for `cache_dir=tmp_path`).

Returns a `Page` with fields: `url`, `final_url`, `status`, `title`,
`markdown`, `html`, `fetched_at`, `fetch_method` (`"static"` |
`"dynamic"`), `content_type`, `char_count`.

---

## `search(query, *, limit=10, backend="ddgs", region=None, settings=None) -> list[SearchResult]`

Backends:

- `"ddgs"` — DuckDuckGo, requires `[discover]` extra.
- `"searxng"` — stub in v0.1.
- `"tavily"` — stub in v0.1.

`SearchResult` fields: `url`, `title`, `snippet`, `rank`, `backend`.

---

## Caching

- Root: `$WEBRIDGE_CACHE_DIR` or `~/.cache/webridge/`.
- Key: `sha256(final_url)[:16]` — **uses final URL after redirects** so
  the same content doesn't cache twice under different inputs.
- Layout: `<prefix[:2]>/<prefix>.md` plus `<prefix>.meta.json`
  (`FetchRecord` JSON).
- No TTL. Housekeep explicitly via `purge()`.

---

## Common patterns

```python
# Research loop: search, then fetch the top N into markdown.
from webridge import search, fetch

for result in search("Samsung Health Sensor SDK", limit=5):
    page = fetch(str(result.url))
    print(page.title, page.char_count)
```

```python
# Tight control of the cache (e.g. isolated test environment):
from webridge import fetch
from webridge._config import WebridgeSettings

settings = WebridgeSettings(cache_dir="/tmp/webridge-test")
page = fetch("https://example.com/", settings=settings)
```

```python
# Housekeeping — drop entries older than 90 days.
from datetime import datetime, timedelta, timezone
from webridge.fetch.cache import purge

purge(older_than=datetime.now(timezone.utc) - timedelta(days=90))
```

---

## Gotchas

- **Playwright binaries.** First use of the dynamic path after install
  needs `playwright install chromium` (~200MB). `fetch_dynamic` raises
  `DynamicFetchError` with a clear message when the binary is missing.
- **Cloudflare / bot challenges.** Some vendor portals (Garmin, Fitbit
  dev) serve a challenge page even to Playwright. The returned `Page`
  will have a low `char_count` and challenge chrome in `markdown`.
- **Encoding.** httpx usually detects correctly; if a page decodes to
  garbage, try `method="dynamic"` or inspect `Page.html` with
  `keep_html=True`.
- **Scientific papers.** Don't try to resolve DOIs or arXiv IDs here.
  Pass the URL through; let the caller route to `paperbridge`.
