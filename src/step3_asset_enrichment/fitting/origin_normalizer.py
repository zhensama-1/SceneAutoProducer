from __future__ import annotations


class OriginNormalizer:
    def bottom_center_origin(self, dimensions: list[float]) -> list[float]:
        return [0.0, 0.0, dimensions[2] / 2.0]
