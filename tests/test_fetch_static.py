from __future__ import annotations

from pathlib import Path

import pytest
from pytest_httpx import HTTPXMock

from webridge._config import WebridgeSettings
from webridge.fetch import fetch
from webridge.fetch.static import fetch_static


def test_static_extracts_article(httpx_mock: HTTPXMock, fixtures_dir: Path):
    html = (fixtures_dir / "sample_article.html").read_text()
    url = "https://example.com/article"
    httpx_mock.add_response(url=url, html=html, headers={"content-type": "text/html"})

    res = fetch_static(url, user_agent="webridge-test/0", timeout=5.0)

    assert res.status == 200
    assert "Sample Article" in res.markdown
    assert len(res.markdown) > 200
    assert res.title and "Sample Article" in res.title
    # Navigation + footer chrome should be stripped by trafilatura.
    assert "Copyright 2026" not in res.markdown


@pytest.mark.httpx_mock(assert_all_responses_were_requested=False)
def test_fetch_auto_uses_static_when_content_is_rich(
    httpx_mock: HTTPXMock, fixtures_dir: Path, tmp_cache_dir: Path, monkeypatch
):
    html = (fixtures_dir / "sample_article.html").read_text()
    url = "https://example.com/article"
    httpx_mock.add_response(url=url, html=html, headers={"content-type": "text/html"})

    settings = WebridgeSettings(cache_dir=tmp_cache_dir)
    page = fetch(url, settings=settings)

    assert page.fetch_method == "static"
    assert page.char_count > 200
    # Second call should come from cache (no new HTTP request needed).
    page2 = fetch(url, settings=settings)
    assert page2.markdown == page.markdown


def test_fetch_static_mode_propagates_http_error(httpx_mock: HTTPXMock, tmp_cache_dir: Path):
    url = "https://example.com/broken"
    httpx_mock.add_response(url=url, status_code=500)

    settings = WebridgeSettings(cache_dir=tmp_cache_dir)
    with pytest.raises(Exception):
        fetch(url, method="static", settings=settings)


@pytest.mark.httpx_mock(assert_all_responses_were_requested=False)
def test_fetch_auto_falls_back_to_dynamic_on_thin_static(
    httpx_mock: HTTPXMock, fixtures_dir: Path, tmp_cache_dir: Path, monkeypatch
):
    """If static extraction returns <200 chars, auto mode should invoke dynamic."""
    html = (fixtures_dir / "empty_spa.html").read_text()
    url = "https://example.com/spa"
    httpx_mock.add_response(url=url, html=html)

    # Stub the dynamic fetcher so we don't need Playwright.
    from webridge.fetch import dynamic as dynamic_mod
    from webridge.fetch.dynamic import DynamicFetchResult

    def fake_dynamic(u: str) -> DynamicFetchResult:
        return DynamicFetchResult(
            url=u,
            final_url=u,
            status=200,
            content_type="text/html",
            html=None,
            markdown="# Rendered by JS\n\n" + ("real content " * 30),
            title="Rendered by JS",
        )

    monkeypatch.setattr(dynamic_mod, "fetch_dynamic", fake_dynamic)

    settings = WebridgeSettings(cache_dir=tmp_cache_dir)
    page = fetch(url, settings=settings)

    assert page.fetch_method == "dynamic"
    assert "Rendered by JS" in page.markdown
