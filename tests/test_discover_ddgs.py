from __future__ import annotations

import pytest


@pytest.mark.network
def test_ddgs_live_search():
    pytest.importorskip("ddgs")
    from webridge.discover.ddgs_backend import search_ddgs

    results = search_ddgs("Polar BLE SDK", limit=3)
    assert 1 <= len(results) <= 3
    assert all(r.backend == "ddgs" for r in results)
    assert all(r.rank >= 1 for r in results)


def test_ddgs_missing_import(monkeypatch):
    import sys

    monkeypatch.setitem(sys.modules, "ddgs", None)
    from webridge.discover.ddgs_backend import search_ddgs

    with pytest.raises(ImportError):
        search_ddgs("anything", limit=1)
