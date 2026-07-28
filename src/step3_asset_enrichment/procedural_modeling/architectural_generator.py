from __future__ import annotations

from src.procedural_modeling.specs import procedural_spec_for_category


class ArchitecturalGenerator:
    def spec(self, category: str, dimensions: list[float]) -> dict:
        return procedural_spec_for_category(category, dimensions)
