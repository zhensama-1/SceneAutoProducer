from __future__ import annotations


def dimensions_are_valid(dimensions: list[float]) -> bool:
    return len(dimensions) == 3 and all(value > 0 for value in dimensions)
