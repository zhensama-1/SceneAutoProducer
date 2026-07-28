from __future__ import annotations

from src.procedural_modeling.fitting import fit_dimensions_to_bbox


class BBoxFitter:
    def fit(self, category: str, scale: list[float], bbox_2d: list[int]) -> list[float]:
        return fit_dimensions_to_bbox(category, scale, bbox_2d)
