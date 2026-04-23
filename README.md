# webridge

Web-content bridge — URL / query → clean markdown, cached, typed.

Sibling to [`paperbridge`](https://github.com/nranthony/paperbridge).
Where paperbridge handles DOIs and scientific metadata, **webridge**
handles the generic web: SDK portals, vendor datasheets, product pages,
anything that's HTML or PDF and not a peer-reviewed paper.

## Status — v0.1

Implemented:

- `fetch(url)` — cache-aware static (httpx + trafilatura) with auto
  fallback to dynamic (Crawl4AI / Playwright).
- `search(query)` — DuckDuckGo via `ddgs`.
- Filesystem cache with sha256-prefix layout, `purge()` housekeeping.
- Pydantic v2 `Page` / `FetchRecord` / `SearchResult` / `SearchQuery`.
- typer CLI: `webridge fetch`, `webridge search`.

Stubbed (raise `NotImplementedError`, wire when a real consumer asks):

- `search(..., backend="searxng")`, `search(..., backend="tavily")`.
- PDF extraction (`webridge.extract.pdf`).

## Install

```bash
uv venv
uv pip install -e ".[dynamic,discover,cli]"
playwright install chromium   # one-off, only needed for the dynamic path
```

Optional extras:

- `dynamic` — Crawl4AI + Playwright (JS-aware fallback)
- `discover` — `ddgs` for DuckDuckGo search
- `pdf` — `pymupdf` / `pymupdf4llm` for PDF → markdown
- `tavily` — Tavily search (paid fallback, stubbed in v0.1)
- `cli` — `typer` CLI
- `all` — everything

## Usage

```python
from webridge import fetch, search

# Cache-aware; auto-routes static (httpx + trafilatura) vs dynamic (Crawl4AI).
page = fetch("https://developer.samsung.com/health/sensor")
print(page.markdown[:500])

# Force the JS path
page = fetch(url, method="dynamic")

# Refresh a stale cache entry
page = fetch(url, refresh=True)

# Discovery
for r in search("Polar BLE SDK", limit=5):
    print(r.rank, r.title, r.url)
```

### Auto-router rule

`fetch(url)` tries the static path first. If the extracted markdown is
shorter than `WEBRIDGE_STATIC_MIN_CHARS` (default 200), it falls back to
the dynamic path and records which was used in `FetchRecord.fetch_method`.
Pass `method="static"` to disable the fallback, `method="dynamic"` to
force the JS path.

### Cache

- Location: `$WEBRIDGE_CACHE_DIR`, or `~/.cache/webridge/` by default.
- Key: `sha256(final_url)[:16]`.
- Layout: `<prefix[:2]>/<prefix>.md` + sibling `.meta.json` holding a `FetchRecord`.
- No TTL. `fetch(url, refresh=True)` forces a refetch; `webridge.fetch.cache.purge(...)` housekeeps.

## CLI

```bash
webridge fetch https://developer.samsung.com/health/sensor > samsung.md
webridge search "Polar BLE SDK"
```

## Environment

All env vars take the `WEBRIDGE_` prefix (also read from a local `.env`):

- `WEBRIDGE_CACHE_DIR`
- `WEBRIDGE_USER_AGENT`
- `WEBRIDGE_REQUEST_TIMEOUT` (seconds)
- `WEBRIDGE_STATIC_MIN_CHARS` (fallback threshold)
- `WEBRIDGE_TAVILY_API_KEY` (or `TAVILY_API_KEY`)
- `WEBRIDGE_SEARXNG_URL` (or `SEARXNG_URL`)

## Development

```bash
uv venv
uv pip install -e ".[discover,cli]" --group dev
.venv/bin/pytest tests/                 # 11 unit + fixture tests (no network)
.venv/bin/pytest -m network tests/      # live-internet tests (opt-in)
.venv/bin/ruff check src/ tests/
.venv/bin/mypy src/webridge
```

The dynamic-fetch tests need the `[dynamic]` extra plus
`playwright install chromium`; they're marked `@pytest.mark.network` and
skipped by default.

See `notebooks/scratch.ipynb` for usage examples.
