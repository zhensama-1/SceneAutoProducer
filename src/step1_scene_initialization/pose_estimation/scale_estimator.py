from __future__ import annotations


class ScaleEstimator:
    def estimate_scale(self, bbox_2d: list[int]) -> list[float]:
        width = max(1, bbox_2d[2] - bbox_2d[0])
        height = max(1, bbox_2d[3] - bbox_2d[1])
        return [max(0.25, width / 260.0), 0.35, max(0.25, height / 240.0)]
