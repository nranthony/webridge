from __future__ import annotations

from datetime import datetime, timezone

import pytest

typer = pytest.importorskip("typer")
from typer.testing import CliRunner  # noqa: E402

from webridge.cli import app  # noqa: E402


def test_cli_fetch_prints_markdown(monkeypatch):
    from webridge.models.page import Page

    fake = Page(
        url="https://example.com/x",
        final_url="https://example.com/x",
        status=200,
        title="X",
        markdown="# hello from cli",
        fetched_at=datetime.now(timezone.utc),
        fetch_method="static",
        content_type="text/html",
        char_count=16,
    )
    monkeypatch.setattr("webridge.cli.fetch_page", lambda url, **kw: fake)

    result = CliRunner().invoke(app, ["fetch", "https://example.com/x"])
    assert result.exit_code == 0
    assert "hello from cli" in result.stdout


def test_cli_search_prints_results(monkeypatch):
    from webridge.models.search import SearchResult

    fakes = [
        SearchResult(url="https://a.test/", title="A", snippet="aa", rank=1, backend="ddgs"),
        SearchResult(url="https://b.test/", title="B", snippet=None, rank=2, backend="ddgs"),
    ]
    monkeypatch.setattr("webridge.cli.search_web", lambda query, **kw: fakes)

    result = CliRunner().invoke(app, ["search", "foo", "-n", "2"])
    assert result.exit_code == 0
    assert "A" in result.stdout and "B" in result.stdout
    assert "https://a.test/" in result.stdout
