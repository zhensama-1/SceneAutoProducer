from __future__ import annotations

from pathlib import Path


class AssetImporter:
    def resolve_path(self, path: str) -> Path:
        return Path(path)
