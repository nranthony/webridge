"""typer-based CLI: ``webridge fetch <url>`` and ``webridge search <query>``."""

from __future__ import annotations

from typing import Optional

try:
    import typer
except ImportError as exc:  # pragma: no cover
    raise ImportError("typer is not installed. Install the 'cli' extra: uv pip install -e \".[cli]\"") from exc

from webridge import fetch as fetch_page
from webridge import search as search_web

app = typer.Typer(add_completion=False, help="webridge — URL/query → clean markdown, cached, typed.")


@app.command("fetch")
def fetch_cmd(
    url: str = typer.Argument(..., help="The URL to fetch."),
    method: str = typer.Option("auto", "--method", "-m", help="auto | static | dynamic"),
    refresh: bool = typer.Option(False, "--refresh", help="Bypass cache."),
) -> None:
    """Fetch a URL and print its markdown to stdout."""
    page = fetch_page(url, method=method, refresh=refresh)  # type: ignore[arg-type]
    typer.echo(page.markdown)


@app.command("search")
def search_cmd(
    query: str = typer.Argument(..., help="Search query."),
    limit: int = typer.Option(10, "--limit", "-n"),
    backend: str = typer.Option("ddgs", "--backend", "-b"),
    region: Optional[str] = typer.Option(None, "--region"),
) -> None:
    """Search the web and print ranked results."""
    results = search_web(query, limit=limit, backend=backend, region=region)  # type: ignore[arg-type]
    for r in results:
        typer.echo(f"{r.rank:>3}  {r.title}")
        typer.echo(f"     {r.url}")
        if r.snippet:
            typer.echo(f"     {r.snippet}")


if __name__ == "__main__":  # pragma: no cover
    app()
