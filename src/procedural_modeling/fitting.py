from __future__ import annotations


def fit_dimensions_to_bbox(category: str, scale: list[float], bbox_2d: list[int]) -> list[float]:
    width, depth, height = scale
    if category in {"table", "desk"}:
        return [max(width, 1.0), max(depth, 0.55), max(height, 0.68)]
    if category in {"cabinet", "shelf", "bookcase"}:
        return [max(width, 0.65), max(depth, 0.32), max(height, 1.1)]
    if category in {"chair"}:
        return [max(width, 0.45), max(depth, 0.45), max(height, 0.75)]
    if category in {"wall"}:
        return [4.0, 0.08, 2.7]
    if category in {"floor"}:
        return [4.0, 3.2, 0.04]
    return [max(width, 0.25), max(depth, 0.25), max(height, 0.25)]
