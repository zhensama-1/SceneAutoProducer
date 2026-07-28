from __future__ import annotations

from src.blender_ir.schema import MaterialIR


class PBRMaterialFactory:
    def create(self, material_id: str, name: str, base_color: list[float], roughness: float = 0.55) -> MaterialIR:
        return MaterialIR(id=material_id, name=name, base_color=base_color, roughness=roughness)
