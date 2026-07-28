from __future__ import annotations


class MeshAligner:
    def align_transform(self, position: list[float], dimensions: list[float]) -> dict:
        return {"position": position, "dimensions": dimensions}
