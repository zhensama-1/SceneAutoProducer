from __future__ import annotations

from src.asset_retrieval.metadata import AssetMetadata


class AssetRanker:
    def rank(self, assets: list[AssetMetadata], dimensions: list[float]) -> list[AssetMetadata]:
        return sorted(assets, key=lambda asset: sum(abs(a - b) for a, b in zip(asset.dimensions, dimensions)))
