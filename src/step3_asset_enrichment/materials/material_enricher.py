from __future__ import annotations

from src.procedural_modeling.materials import infer_material_for_category


class MaterialEnricher:
    def infer(self, category: str, scene_style: str = "neutral"):
        return infer_material_for_category(category, scene_style)
