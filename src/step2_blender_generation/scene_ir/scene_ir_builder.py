from __future__ import annotations

from pathlib import Path

from src.asset_retrieval.metadata import AssetLibrary
from src.scene_planner.planner import ScenePlannerAgent
from src.step2_blender_generation.schemas import BlenderSceneIR


class SceneIRBuilder:
    def __init__(self, asset_library: AssetLibrary | None = None, scene_style: str = "neutral"):
        self.planner = ScenePlannerAgent(asset_library=asset_library, scene_style=scene_style)

    def build(self, initialization: dict, output_root: Path, exports: list[str] | None = None) -> BlenderSceneIR:
        return self.planner.plan(initialization, output_root, exports=exports)
