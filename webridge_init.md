# `webridge` — init brief for Claude Code

This document bootstraps a new Python package that sits alongside
[`paperbridge`](https://github.com/nranthony/paperbridge) and handles the
**generic web-content → clean markdown → pydantic** job. Drop this file
into the root of a fresh, empty repo, open Claude Code, and say:
*"Follow `webridge_init.md` and bootstrap the repo."*

Everything Claude Code needs to stand up the scaffolding, wire
dependencies, and implement the v0.1 surface is below.

---

## 1. Mission

`webridge` does for arbitrary web pages what `paperbridge` does for
scientific papers: takes an identifier (here a URL, or a search query)
and returns a normalised, cached, LLM-consumable representation.

**In scope (v0.1):**

- URL → clean markdown (JS-aware fallback via Crawl4AI; static fast path via httpx + trafilatura).
- Query → list of candidate URLs (DuckDuckGo via `ddgs`; SearXNG client; Tavily as paid fallback).
- Hash-keyed filesystem cache so re-runs are free and idempotent.
- Pydantic `Page`, `SearchResult`, `FetchRecord` models — typed at every boundary.
- Thin CLI: `webridge fetch <url>` and `webridge search <query>`.

**Out of scope (explicitly):**

- Scientific papers — that's `paperbridge`'s job. If a URL happens to be
  a DOI or arXiv link, do not try to resolve it here; return the page as
  fetched and let the caller route to paperbridge.
- LLM-assisted structured extraction (typed-record synthesis). Tempting
  but premature; add only when a second consumer asks for it.
- Full-site crawl / sitemap-driven crawl. Single-URL fetch only in v0.1.
- Auth'd scraping (login walls, OAuth). Defer.

## 2. Conventions (mirror paperbridge)

- **Python 3.12+**, `uv` for venv and package management.
- **Build backend:** `setuptools` (match paperbridge) OR `hatchling` — pick
  setuptools for consistency with paperbridge unless there's a reason not to.
- **Logging:** `loguru` only. Expose `_logging.py` with the same
  configure-once pattern paperbridge uses.
- **Config:** `pydantic-settings` with a `WEBRIDGE_` env var prefix
  (cache dir, API keys, default user-agent).
- **Models:** pydantic v2, strict types, no `Any`.
- **Ruff + mypy** with the same config as paperbridge (line-length 120,
  target py312, mypy non-strict but `warn_return_any`).
- **Tests:** `pytest` + `pytest-mock`. Network-touching tests marked
  `@pytest.mark.network` and skipped by default in CI.
- **Optional-deps groups** mirror paperbridge's style (`[project.optional-dependencies]`
  for runtime extras, `[dependency-groups]` for dev tooling).

## 3. Repo bootstrap (first pass)

Claude Code should create this layout:

```
webridge/
├── .gitignore                # match paperbridge's
├── .python-version           # 3.12
├── LICENSE                   # MIT (match paperbridge)
├── README.md                 # written from §9 of this file
├── AGENTS.md                 # copy paperbridge's verbatim; add any webridge-specific agent rules
├── CLAUDE.md                 # short: points to AGENTS.md and this init doc
├── pyproject.toml            # see §4
├── src/
│   └── webridge/
│       ├── __init__.py       # re-export public API
│       ├── py.typed          # empty marker file
│       ├── _config.py        # WebridgeSettings (pydantic-settings)
│       ├── _logging.py       # loguru setup
│       ├── models/
│       │   ├── __init__.py
│       │   ├── page.py       # Page, FetchRecord
│       │   └── search.py     # SearchResult, SearchQuery
│       ├── fetch/
│       │   ├── __init__.py   # fetch(url, **opts) top-level
│       │   ├── static.py     # httpx + trafilatura
│       │   ├── dynamic.py    # Crawl4AI wrapper
│       │   └── cache.py      # hash-keyed filesystem cache
│       ├── discover/
│       │   ├── __init__.py   # search(query, backend=...)
│       │   ├── ddgs_backend.py
│       │   ├── searxng_backend.py
│       │   └── tavily_backend.py
│       ├── extract/
│       │   ├── __init__.py
│       │   ├── html.py       # HTML → markdown (trafilatura / markdownify)
│       │   └── pdf.py        # PDF → text (pymupdf) — optional extra
│       └── cli.py            # typer or argparse CLI
├── tests/
│   ├── conftest.py           # fixtures, network-skip marker
│   ├── test_cache.py
│   ├── test_fetch_static.py
│   ├── test_fetch_dynamic.py  # @pytest.mark.network
│   ├── test_discover_ddgs.py  # @pytest.mark.network
│   └── fixtures/              # saved HTML/PDF samples for offline tests
└── notebooks/
    └── scratch.ipynb          # usage examples
```

## 4. `pyproject.toml`

```toml
[build-system]
requires = ["setuptools>=68.0"]
build-backend = "setuptools.build_meta"

[project]
name = "webridge"
version = "0.1.0"
description = "Web-content bridge — URL/query → clean markdown, cached, typed"
requires-python = ">=3.12"
license = {text = "MIT"}
authors = [{name = "Neil Anthony"}]
dependencies = [
    "pydantic>=2.0",
    "pydantic-settings>=2.0",
    "httpx>=0.27",
    "loguru>=0.7",
    "trafilatura>=1.9",
    "markdownify>=0.11",
]

[project.optional-dependencies]
dynamic = ["crawl4ai>=0.4", "playwright>=1.40"]
discover = ["ddgs>=6.0"]
pdf = ["pymupdf>=1.23", "pymupdf4llm>=0.0.10"]
tavily = ["tavily-python>=0.3"]
cli = ["typer>=0.12"]
all = ["webridge[dynamic,discover,pdf,tavily,cli]"]

[project.scripts]
webridge = "webridge.cli:app"

[dependency-groups]
dev = ["pytest>=7.0", "pytest-mock", "pytest-httpx", "ruff", "mypy"]
notebook = ["ipykernel", "ipywidgets"]
all-dev = [{include-group = "dev"}, {include-group = "notebook"}]

[tool.setuptools.packages.find]
where = ["src"]

[tool.pytest.ini_options]
markers = [
    "network: tests that hit the live internet (skipped by default)",
]
addopts = "-m 'not network'"

[tool.ruff]
target-version = "py312"
line-length = 120

[tool.mypy]
python_version = "3.12"
strict = false
warn_return_any = true
warn_unused_configs = true
```

Base install is lightweight (httpx + trafilatura). JS rendering
(`dynamic`), search (`discover`), PDF handling (`pdf`), paid fallbacks
(`tavily`), and CLI (`cli`) are all opt-in.

## 5. Pydantic models (v0.1 surface)

```python
# src/webridge/models/page.py
from datetime import datetime
from pydantic import BaseModel, Field, HttpUrl


class Page(BaseModel):
    url: HttpUrl
    final_url: HttpUrl            # after redirects
    status: int
    title: str | None
    markdown: str                 # clean, LLM-ready
    html: str | None = None       # optional raw
    fetched_at: datetime
    fetch_method: str             # "static" | "dynamic"
    content_type: str | None
    char_count: int = Field(..., ge=0)


class FetchRecord(BaseModel):
    """Metadata about a fetch attempt, cached to disk alongside the page."""
    url: HttpUrl
    cache_path: str
    fetched_at: datetime
    fetch_method: str
    elapsed_ms: int
    from_cache: bool
    error: str | None = None
```

```python
# src/webridge/models/search.py
from pydantic import BaseModel, HttpUrl


class SearchResult(BaseModel):
    url: HttpUrl
    title: str
    snippet: str | None
    rank: int
    backend: str                  # "ddgs" | "searxng" | "tavily"


class SearchQuery(BaseModel):
    query: str
    limit: int = 10
    backend: str = "ddgs"
    region: str | None = None     # e.g. "us-en"
```

## 6. Core API (v0.1)

```python
from webridge import fetch, search, Page, SearchResult

# Simple: cache-aware, auto-routes static vs dynamic
page: Page = fetch("https://developer.samsung.com/health/sensor")

# Force the JS path
page = fetch(url, method="dynamic")

# Discovery
results: list[SearchResult] = search("Samsung Health Sensor SDK", limit=5)

# Refresh a stale cache entry
page = fetch(url, refresh=True)
```

Internal routing rule: `fetch()` tries static first (httpx + trafilatura).
If the extracted markdown is <200 chars or trafilatura flags low
extraction quality, it falls back to the `dynamic` (Crawl4AI) path and
records which was used in `FetchRecord.fetch_method`. The auto-fallback
can be disabled with `method="static"` or forced with `method="dynamic"`.

## 7. Cache design

- Location: `$WEBRIDGE_CACHE_DIR` or platform default
  (`~/.cache/webridge/` on Linux/macOS).
- Key: `sha256(final_url)[:16]`.
- Layout: `cache/{prefix[:2]}/{prefix}.md` plus sibling `{prefix}.meta.json`
  holding `FetchRecord` for provenance.
- **No TTL** — cache is permanent until `refresh=True` or manual purge. Web
  content is stable enough for research reruns; TTL complicates reasoning.
- Expose `webridge.cache.purge(url=..., older_than=...)` for housekeeping.

## 8. Source material to port

Two files already exist in the sibling `wearable_data_testing` repo
(where this init brief was authored). Lift them as the starting point:

- `/Volumes/DataDrive/repo/therapod/wearable_data_testing/scripts/fetch_url.py`
  — the minimum-viable Crawl4AI + filesystem-cache wrapper. Becomes the
  core of `webridge/fetch/dynamic.py` + `webridge/fetch/cache.py`.
  Keep the sha256-prefix naming scheme.
- Any search helpers that accumulate under
  `wearable_data_testing/src/weardata/web/` during the ongoing wearable
  research run. Check there before writing from scratch.

After the port, leave a one-line note in the wearable project's
`CLAUDE.md` pointing to the new `webridge` repo so future agents find
the canonical location.

## 9. README (draft for the new repo)

```markdown
# webridge

Web-content bridge — URL / query → clean markdown, cached, typed.

Sibling to [`paperbridge`](https://github.com/nranthony/paperbridge).
Where paperbridge handles DOIs and scientific metadata, webridge
handles the generic web: SDK portals, vendor datasheets, product pages,
anything that's HTML or PDF and not a peer-reviewed paper.

## Install

```bash
uv pip install -e ".[dynamic,discover,cli]"
playwright install chromium   # one-off, needed for the dynamic path
```

## Usage

```python
from webridge import fetch, search

page = fetch("https://developer.samsung.com/health/sensor")
print(page.markdown[:500])

for r in search("Polar BLE SDK", limit=5):
    print(r.rank, r.title, r.url)
```

CLI:

```bash
webridge fetch https://developer.samsung.com/health/sensor > samsung.md
webridge search "Polar BLE SDK"
```

See `notebooks/scratch.ipynb` for more.
```

## 10. Implementation checklist (work in this order)

1. **Scaffold** — repo layout from §3, empty module files, `pyproject.toml`
   from §4, `.venv` via `uv venv`, `uv pip install -e ".[all-dev]"`.
2. **Models** — `page.py`, `search.py` per §5. Add doctest-style examples.
3. **Cache** — port `fetch_url.py`'s caching into `fetch/cache.py`.
   Unit test with a temp dir fixture (offline).
4. **Static fetch** — `fetch/static.py` using httpx + trafilatura.
   Fixture-based tests (saved HTML in `tests/fixtures/`).
5. **Dynamic fetch** — `fetch/dynamic.py` wrapping Crawl4AI. Behind the
   `dynamic` extra so base install stays light. One network test
   (marked).
6. **Auto-router** — top-level `fetch()` that tries static then falls
   back. Test the fallback decision logic with mocks.
7. **Discover — ddgs** — `discover/ddgs_backend.py`. Network test
   marked.
8. **CLI** — `typer`-based, two commands (`fetch`, `search`). Exercise
   via `pytest` with `CliRunner`.
9. **README + scratch notebook** — match paperbridge's shape.
10. **SearXNG and Tavily backends** — only if you actually need them.
    Skip if ddgs covers the discovery need.
11. **PDF extract** — only if the first real consumer (wearable research
    run) demands it.

Stop after step 9 and use it on a real task (the wearable SDK research
in the sibling repo). Steps 10–11 are speculative; don't pre-build.

## 11. Testing strategy

- **Unit (default, no network):** cache round-trip, model validation,
  router decision logic, CLI parsing.
- **Fixture-based integration:** saved HTML/PDF in `tests/fixtures/`
  piped through the static extractor. Catches trafilatura regressions.
- **Network (opt-in via `pytest -m network`):** one live fetch per
  backend. Run locally before release; skip in CI unless a
  `LIVE=1` env var is set.

## 12. Known gotchas to document in-code

- **Playwright binaries.** First `crawl4ai` run after install needs
  `playwright install chromium` (~200MB). `fetch/dynamic.py` should
  raise a clear error pointing to that command if the binary is missing.
- **Cloudflare / bot protection.** Some vendor portals (seen with
  Garmin, Fitbit dev) serve a challenge page even to Playwright. Record
  `status` and a flag in `FetchRecord.error`; don't retry silently.
- **Robots.txt.** Default to respecting it; expose
  `webridge.fetch(url, ignore_robots=True)` for research use where the
  user accepts responsibility. Log the override.
- **Encoding.** httpx doesn't always detect encoding correctly for older
  vendor PDFs/HTML. Fall back to `chardet` if the decoded content has
  >5% replacement chars.
- **URL normalisation.** Cache keys must use the *final* URL (post-redirect),
  not the input. Otherwise the same content caches twice under different
  keys.

## 13. When to extract from this brief

Treat this file as the source of truth until the repo exists. Once the
scaffolding is up:

- Delete this file from the new repo and keep only `README.md` + `AGENTS.md`.
- Keep a copy of this init brief in the `wearable_data_testing` repo
  (where it originated) as a record of intent.
- Update `paperbridge`'s README with a one-line "see also: webridge"
  link so future users find both halves of the bridge pair.

## 14. Non-goals worth restating

- Don't build a generic web framework. Two jobs only: *fetch a URL*,
  *search for URLs*. Everything else is the caller's problem.
- Don't add LLM calls. This library returns markdown; extraction into
  typed records belongs one layer up.
- Don't add a database. Filesystem cache is sufficient; adding SQLite
  forces schema migrations the library doesn't need.
- Don't ship browser-automation features beyond what Crawl4AI already
  does. If someone needs click-through flows, they should reach for
  Playwright directly.
