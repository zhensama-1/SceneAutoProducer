from __future__ import annotations


class ScaleSolver:
    def solve(self, source_dimensions: list[float], target_dimensions: list[float]) -> list[float]:
        return [target / source if source else 1.0 for source, target in zip(source_dimensions, target_dimensions)]
