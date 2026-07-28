from __future__ import annotations

from src.step2_blender_generation.schemas import BlenderSceneIR


class EnrichedSceneBuilder:
    def build(self, ir: BlenderSceneIR) -> BlenderSceneIR:
        return ir
