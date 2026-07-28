from __future__ import annotations


def grounded_position(position: list[float], dimensions: list[float]) -> list[float]:
    adjusted = list(position)
    adjusted[2] = dimensions[2] / 2.0
    return adjusted
