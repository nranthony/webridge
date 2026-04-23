"""Hash-keyed filesystem cache for fetched pages.

Layout::

    <cache_dir>/{prefix[:2]}/{prefix}.md       # markdown body
    <cache_dir>/{prefix[:2]}/{prefix}.meta.json  # FetchRecord JSON

The cache key is ``sha256(final_url)[:16]``. Using the *final* URL (after
redirects) avoids duplicate entries for the same content under different
input URLs.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable, Optional

from webridge._logging import get_logger
from webridge.models.page import FetchRecord

logger = get_logger(__name__)


def _key(url: str) -> str:
    return hashlib.sha256(url.encode("utf-8")).hexdigest()[:16]


def _paths(cache_dir: Path, url: str) -> tuple[Path, Path]:
    k = _key(url)
    sub = cache_dir / k[:2]
    return sub / f"{k}.md", sub / f"{k}.meta.json"


@dataclass(slots=True)
class CachedEntry:
    markdown: str
    record: FetchRecord


class Cache:
    """Filesystem cache. Stateless except for the root directory."""

    def __init__(self, cache_dir: Path):
        self.cache_dir = Path(cache_dir)

    def path_for(self, url: str) -> Path:
        return _paths(self.cache_dir, url)[0]

    def get(self, url: str) -> Optional[CachedEntry]:
        md_path, meta_path = _paths(self.cache_dir, url)
        if not md_path.exists() or not meta_path.exists():
            return None
        try:
            markdown = md_path.read_text(encoding="utf-8")
            record = FetchRecord.model_validate_json(meta_path.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            logger.warning("cache read failed for {}: {}", url, exc)
            return None
        logger.debug("cache hit {}", url)
        return CachedEntry(markdown=markdown, record=record)

    def put(self, url: str, markdown: str, record: FetchRecord) -> Path:
        md_path, meta_path = _paths(self.cache_dir, url)
        md_path.parent.mkdir(parents=True, exist_ok=True)
        md_path.write_text(markdown, encoding="utf-8")
        meta_path.write_text(record.model_dump_json(indent=2), encoding="utf-8")
        logger.debug("cache write {} -> {}", url, md_path)
        return md_path

    def purge(
        self,
        *,
        url: Optional[str] = None,
        older_than: Optional[datetime] = None,
    ) -> int:
        """Delete cache entries. Returns the number of entries removed.

        - ``url``: delete exactly one entry.
        - ``older_than``: delete entries whose ``fetched_at`` predates this.
        - Neither: delete everything under ``cache_dir``.
        """
        if url is not None:
            md_path, meta_path = _paths(self.cache_dir, url)
            removed = 0
            for p in (md_path, meta_path):
                if p.exists():
                    p.unlink()
                    removed += 1
            return 1 if removed else 0

        removed = 0
        for meta in self._iter_meta():
            if older_than is not None:
                try:
                    record = FetchRecord.model_validate_json(meta.read_text(encoding="utf-8"))
                except (OSError, ValueError):
                    continue
                if record.fetched_at >= older_than:
                    continue
            md = meta.with_suffix("").with_suffix(".md")
            for p in (md, meta):
                if p.exists():
                    p.unlink()
            removed += 1
        return removed

    def _iter_meta(self) -> Iterable[Path]:
        if not self.cache_dir.exists():
            return []
        return self.cache_dir.rglob("*.meta.json")


def purge(
    *,
    url: Optional[str] = None,
    older_than: Optional[datetime] = None,
    cache_dir: Optional[Path] = None,
) -> int:
    """Module-level convenience — see :meth:`Cache.purge`."""
    from webridge._config import WebridgeSettings

    root = cache_dir if cache_dir is not None else WebridgeSettings().cache_dir
    return Cache(root).purge(url=url, older_than=older_than)
