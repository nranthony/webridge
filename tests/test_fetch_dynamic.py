from __future__ import annotations

import pytest


@pytest.mark.network
def test_dynamic_fetch_live():
    """Live Crawl4AI fetch. Requires [dynamic] extra + `playwright install chromium`."""
    pytest.importorskip("crawl4ai")
    from webridge.fetch.dynamic import fetch_dynamic

    res = fetch_dynamic("https://example.com/")
    assert res.status in (200, 0)
    assert res.markdown
