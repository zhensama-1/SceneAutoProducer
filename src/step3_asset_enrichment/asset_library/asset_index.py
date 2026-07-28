from __future__ import annotations

from src.asset_retrieval.metadata import AssetLibrary, AssetMetadata


class AssetIndex:
    def __init__(self, library: AssetLibrary):
        self.library = library

    def by_category(self, category: str) -> list[AssetMetadata]:
        return self.library.by_category(category)
