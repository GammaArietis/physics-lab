"""Portable serialization helpers for repository artifacts."""

from __future__ import annotations

from pathlib import Path


_REPOSITORY_ROOT = Path(__file__).resolve().parents[3]


def portable_path(path: Path, *, anchor: Path | None = None) -> str:
    """Return a stable POSIX path relative to the repository or an explicit run root."""

    resolved = path.resolve()
    root = _REPOSITORY_ROOT if anchor is None else anchor.resolve()
    try:
        relative = resolved.relative_to(root)
    except ValueError as exc:
        raise ValueError(f"artifact path is outside repository: {resolved}") from exc
    return relative.as_posix()

