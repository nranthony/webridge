"""webridge — web-content bridge. URL/query → clean markdown, cached, typed."""

from webridge.fetch import fetch
from webridge.discover import search
from webridge.models import FetchRecord, Page, SearchQuery, SearchResult

__all__ = ["fetch", "search", "Page", "FetchRecord", "SearchResult", "SearchQuery"]
__version__ = "0.1.0"
