"""PDF → text helpers — behind the ``[pdf]`` optional extra. Stub for v0.1."""

from __future__ import annotations

from pathlib import Path


def pdf_to_markdown(path: Path) -> str:
    try:
        import pymupdf4llm  # type: ignore[import-not-found]
    except ImportError as exc:
        raise ImportError("pymupdf4llm is not installed. Install the 'pdf' extra.") from exc
    return str(pymupdf4llm.to_markdown(str(path)))
