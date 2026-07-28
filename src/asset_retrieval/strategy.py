from __future__ import annotations


class AssetStrategyPlanner:
    """Chooses a geometry strategy per semantic object."""

    PROCEDURAL_CATEGORIES = {
        "floor",
        "wall",
        "ceiling",
        "door",
        "window",
        "table",
        "desk",
        "cabinet",
        "shelf",
        "bookcase",
    }
    ASSET_CATEGORIES = {
        "chair",
        "sofa",
        "lamp",
        "plant",
        "vase",
        "decor",
        "bed",
        "monitor",
        "keyboard",
    }

    def choose(self, category: str, has_asset: bool, confidence: float) -> str:
        if category in self.PROCEDURAL_CATEGORIES:
            return "procedural_modeling"
        if category in self.ASSET_CATEGORIES and has_asset:
            return "replace_with_asset"
        if category in self.ASSET_CATEGORIES and confidence < 0.75:
            return "hybrid"
        if confidence < 0.45:
            return "procedural_modeling"
        return "keep_reconstructed_mesh"
