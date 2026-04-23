"""Search models."""

from typing import Literal, Optional

from pydantic import BaseModel, Field, HttpUrl

SearchBackend = Literal["ddgs", "searxng", "tavily"]


class SearchResult(BaseModel):
    url: HttpUrl
    title: str
    snippet: Optional[str] = None
    rank: int = Field(..., ge=1)
    backend: SearchBackend


class SearchQuery(BaseModel):
    query: str
    limit: int = Field(10, ge=1, le=100)
    backend: SearchBackend = "ddgs"
    region: Optional[str] = None
