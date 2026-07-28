from __future__ import annotations

from src.procedural_modeling.specs import procedural_spec_for_category


class RoomGenerator:
    def floor_spec(self, dimensions: list[float]) -> dict:
        return procedural_spec_for_category("floor", dimensions)

    def wall_spec(self, dimensions: list[float]) -> dict:
        return procedural_spec_for_category("wall", dimensions)
