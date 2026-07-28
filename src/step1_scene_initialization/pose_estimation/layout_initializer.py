from __future__ import annotations


class LayoutInitializer:
    def estimate_position(self, bbox_2d: list[int], dimensions: list[float]) -> list[float]:
        center_x = (bbox_2d[0] + bbox_2d[2]) / 2.0
        normalized_x = (center_x - 320.0) / 180.0
        return [normalized_x, 0.0, dimensions[2] / 2.0]
