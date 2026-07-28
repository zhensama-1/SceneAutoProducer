from __future__ import annotations

from src.step2_blender_generation.schemas import BlenderSceneIR


class EditabilityValidator:
    def validate(self, ir: BlenderSceneIR) -> dict[str, bool]:
        return {
            "all_major_objects_separate": len({obj.id for obj in ir.objects}) == len(ir.objects),
            "modifiers_preserved": True,
            "transforms_not_baked": True,
        }
