from __future__ import annotations

from .metadata import AssetLibrary, AssetMetadata


class AssetRetriever:
    def __init__(self, library: AssetLibrary):
        self.library = library

    def find_best(self, category: str, dimensions: list[float], style: str = "generic") -> AssetMetadata | None:
        candidates = self.library.by_category(category)
        if not candidates:
            return None

        def score(asset: AssetMetadata) -> tuple[float, int]:
            style_bonus = 0.0 if asset.style == style or style == "generic" else 0.25
            dimension_error = sum(abs(a - b) for a, b in zip(asset.dimensions, dimensions))
            poly_penalty = asset.poly_count / 1_000_000.0
            return (dimension_error + style_bonus + poly_penalty, asset.poly_count)

        return sorted(candidates, key=score)[0]
