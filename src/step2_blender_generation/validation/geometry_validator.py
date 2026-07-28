from __future__ import annotations

from src.step2_blender_generation.schemas import BlenderSceneIR


class GeometryValidator:
    def floating_objects(self, ir: BlenderSceneIR) -> list[str]:
        return [
            obj.id
            for obj in ir.objects
            if obj.category not in {"wall", "ceiling"} and obj.transform.position[2] - obj.dimensions[2] / 2.0 > 0.05
        ]
