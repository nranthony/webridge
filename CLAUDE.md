# CLAUDE.md

Guidance for Claude Code when working in this repo.

## Project purpose

`webridge` is a standalone Python library that turns a URL (or a search
query) into clean, cached, typed markdown. Sibling to
[`paperbridge`](https://github.com/nranthony/paperbridge) — where
paperbridge handles DOIs and scientific metadata, webridge handles the
generic web (SDK portals, vendor datasheets, product pages, HTML/PDF).

Read `AGENTS.md` for a compact, task-oriented API reference.

## Status — v0.1

Implemented and green (11/11 tests, ruff + mypy clean):

- `fetch()` auto-router (static → dynamic fallback at `< WEBRIDGE_STATIC_MIN_CHARS`).
- Static path: httpx + trafilatura, `keep_html=True` opt-in.
- Dynamic path: Crawl4AI wrapper, behind `[dynamic]` extra.
- Filesystem cache (`Cache` class + module-level `purge()`).
- ddgs search backend.
- typer CLI behind `[cli]` extra.

Stubbed only — `NotImplementedError` until a consumer asks:

- `discover/searxng_backend.py`, `discover/tavily_backend.py`.
- `extract/pdf.py` (skeleton; `[pdf]` extra not wired into `fetch()`).

`webridge_init.md` is the original brief and can be removed once you're
happy with the scaffold.

## Development

```bash
uv venv
uv pip install -e ".[discover,cli]" --group dev
# add ".[dynamic]" + `playwright install chromium` for the JS path

.venv/bin/pytest tests/                 # 11 unit/fixture tests, no network
.venv/bin/pytest -m network tests/      # opt-in live-internet tests
.venv/bin/ruff check src/ tests/
.venv/bin/mypy src/webridge
```

## Architecture

- `fetch/` — URL → `Page`. `fetch/__init__.py:fetch()` is the top-level
  auto-router that tries `static.py` (httpx + trafilatura) first, then
  falls back to `dynamic.py` (Crawl4AI / Playwright) if the static result
  is thin. `cache.py` is a sha256-prefix filesystem cache.
- `discover/` — query → `list[SearchResult]`. Dispatch in
  `__init__.py:search()` across backends. Only `ddgs_backend` is
  implemented; `searxng_backend` and `tavily_backend` are stubs.
- `extract/` — HTML → markdown (`html.py`) and PDF → markdown (`pdf.py`)
  helpers. Thin wrappers around trafilatura / markdownify / pymupdf4llm.
- `models/` — pydantic v2 `Page`, `FetchRecord`, `SearchResult`, `SearchQuery`.
- `_config.py` — `WebridgeSettings` (pydantic-settings, `WEBRIDGE_` prefix).
  No global singleton.
- `_logging.py` — `get_logger(name)` — loguru, never calls `logger.remove()` globally.
- `cli.py` — typer, behind `[cli]` extra.

## Conventions

- **Python 3.12+**, `uv` for venv + deps.
- **Logging**: `from webridge._logging import get_logger; logger = get_logger(__name__)`.
- **Pydantic v2**, strict types. No `Any`.
- **Optional deps are truly optional**: guard every `crawl4ai` / `ddgs` /
  `pymupdf4llm` / `tavily` / `typer` import with `try/except ImportError`
  and raise a clear message pointing to the extra.
- **Cache keys use the *final* URL** (post-redirect), not the input.
- **Network tests marked `@pytest.mark.network`** and skipped by default
  (`pyproject.toml` sets `addopts = -m 'not network'`).
- **mypy uses the `pydantic.mypy` plugin** so `WebridgeSettings()` and
  pydantic-model construction with `str` URLs type-check correctly.
- **Don't import `fetch_dynamic` by name into `fetch/__init__.py`** —
  import the `dynamic` submodule and call `_dynamic.fetch_dynamic(...)`.
  Keeps `monkeypatch.setattr(dynamic_mod, "fetch_dynamic", ...)` working
  in tests instead of patching a stale local binding.

## Out of scope (don't add without asking)

- Scientific-paper handling (DOI/arXiv resolution) — that's `paperbridge`.
- LLM-assisted structured extraction.
- Full-site crawls / sitemap walking.
- Auth'd scraping (login walls, OAuth).
- A database. Filesystem cache is enough.
