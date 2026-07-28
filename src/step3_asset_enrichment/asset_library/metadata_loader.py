from __future__ import annotations

from pathlib import Path

from src.asset_retrieval.metadata import AssetLibrary


class MetadataLoader:
    def load(self, path: Path) -> AssetLibrary:
        return AssetLibrary.load(path)
