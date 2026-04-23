"""Page + FetchRecord models."""

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field, HttpUrl

FetchMethod = Literal["static", "dynamic"]


class Page(BaseModel):
    """A fetched, normalised web page.

    ``markdown`` is the LLM-ready content; ``html`` is retained only when
    the caller asks for it (opt-in via ``fetch(..., keep_html=True)``).
    """

    url: HttpUrl
    final_url: HttpUrl
    status: int
    title: Optional[str] = None
    markdown: str
    html: Optional[str] = None
    fetched_at: datetime
    fetch_method: FetchMethod
    content_type: Optional[str] = None
    char_count: int = Field(..., ge=0)


class FetchRecord(BaseModel):
    """Metadata about a fetch attempt, cached alongside the page."""

    url: HttpUrl
    final_url: Optional[HttpUrl] = None
    cache_path: str
    fetched_at: datetime
    fetch_method: FetchMethod
    elapsed_ms: int = Field(..., ge=0)
    from_cache: bool
    status: Optional[int] = None
    error: Optional[str] = None
