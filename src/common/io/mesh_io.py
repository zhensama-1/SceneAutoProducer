from __future__ import annotations

from pathlib import Path


def require_mesh(path: Path) -> Path:
    if not path.exists():
        raise FileNotFoundError(path)
    return path
