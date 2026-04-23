from __future__ import annotations

from datetime import datetime, timedelta, timezone

from webridge.fetch.cache import Cache
from webridge.models.page import FetchRecord


def _record(url: str, cache_path: str, fetched_at: datetime) -> FetchRecord:
    return FetchRecord(
        url=url,
        final_url=url,
        cache_path=cache_path,
        fetched_at=fetched_at,
        fetch_method="static",
        elapsed_ms=12,
        from_cache=False,
        status=200,
    )


def test_cache_roundtrip(tmp_cache_dir):
    cache = Cache(tmp_cache_dir)
    url = "https://example.com/page"
    now = datetime.now(timezone.utc)
    record = _record(url, str(cache.path_for(url)), now)

    assert cache.get(url) is None
    cache.put(url, "# hello\n\nbody", record)

    got = cache.get(url)
    assert got is not None
    assert got.markdown.startswith("# hello")
    assert str(got.record.url) == url
    assert got.record.fetch_method == "static"


def test_cache_purge_by_url(tmp_cache_dir):
    cache = Cache(tmp_cache_dir)
    url = "https://example.com/page"
    now = datetime.now(timezone.utc)
    cache.put(url, "content", _record(url, str(cache.path_for(url)), now))

    removed = cache.purge(url=url)
    assert removed == 1
    assert cache.get(url) is None


def test_cache_purge_older_than(tmp_cache_dir):
    cache = Cache(tmp_cache_dir)
    old_url = "https://example.com/old"
    new_url = "https://example.com/new"
    now = datetime.now(timezone.utc)
    cache.put(old_url, "old", _record(old_url, str(cache.path_for(old_url)), now - timedelta(days=30)))
    cache.put(new_url, "new", _record(new_url, str(cache.path_for(new_url)), now))

    removed = cache.purge(older_than=now - timedelta(days=7))
    assert removed == 1
    assert cache.get(old_url) is None
    assert cache.get(new_url) is not None


def test_cache_key_uses_url_hash(tmp_cache_dir):
    cache = Cache(tmp_cache_dir)
    p1 = cache.path_for("https://example.com/a")
    p2 = cache.path_for("https://example.com/b")
    assert p1 != p2
    assert p1.suffix == ".md"
    # sha256 prefix = 16 hex chars + .md
    assert len(p1.stem) == 16
