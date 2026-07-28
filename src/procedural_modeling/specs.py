from __future__ import annotations


def procedural_spec_for_category(category: str, dimensions: list[float]) -> dict:
    if category in {"table", "desk"}:
        return {
            "kind": "table",
            "dimensions": dimensions,
            "top_thickness": min(0.08, dimensions[2] * 0.12),
            "leg_thickness": min(0.08, max(0.04, min(dimensions[0], dimensions[1]) * 0.08)),
            "bevel": 0.015,
        }
    if category in {"cabinet", "shelf", "bookcase"}:
        shelves = 3 if dimensions[2] < 1.5 else 4
        return {
            "kind": "cabinet",
            "dimensions": dimensions,
            "shelf_count": shelves,
            "board_thickness": 0.045,
            "bevel": 0.01,
        }
    if category == "wall":
        return {"kind": "wall", "dimensions": dimensions, "bevel": 0.0}
    if category == "floor":
        return {"kind": "floor", "dimensions": dimensions, "bevel": 0.0}
    return {"kind": "box", "dimensions": dimensions, "bevel": 0.01}
