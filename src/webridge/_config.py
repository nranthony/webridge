"""WeBridge settings — env-driven config for cache, HTTP, and API keys."""

from pathlib import Path
from typing import Optional

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings


def _default_cache_dir() -> Path:
    return Path.home() / ".cache" / "webridge"


class WebridgeSettings(BaseSettings):
    """Configuration loaded from environment variables or ``.env``.

    All env vars use the ``WEBRIDGE_`` prefix. No global singleton —
    instantiate per caller.
    """

    cache_dir: Path = Field(
        default_factory=_default_cache_dir,
        validation_alias=AliasChoices("WEBRIDGE_CACHE_DIR", "webridge_cache_dir"),
    )
    user_agent: str = Field(
        "webridge/0.1 (+https://github.com/nranthony/webridge)",
        validation_alias=AliasChoices("WEBRIDGE_USER_AGENT", "webridge_user_agent"),
    )
    request_timeout: int = Field(
        30,
        validation_alias=AliasChoices("WEBRIDGE_REQUEST_TIMEOUT", "webridge_request_timeout"),
    )
    static_min_chars: int = Field(
        200,
        validation_alias=AliasChoices("WEBRIDGE_STATIC_MIN_CHARS", "webridge_static_min_chars"),
        description="Static-extract markdown shorter than this triggers the dynamic fallback.",
    )
    tavily_api_key: Optional[str] = Field(
        None,
        validation_alias=AliasChoices("WEBRIDGE_TAVILY_API_KEY", "TAVILY_API_KEY", "tavily_api_key"),
    )
    searxng_url: Optional[str] = Field(
        None,
        validation_alias=AliasChoices("WEBRIDGE_SEARXNG_URL", "SEARXNG_URL", "searxng_url"),
    )

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
        "extra": "ignore",
        "populate_by_name": True,
    }
