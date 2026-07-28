from __future__ import annotations

from pathlib import Path

from src.step2_blender_generation.schemas import BlenderSceneIR
from src.validation.report import validate_outputs


class SceneValidator:
    def validate(self, ir: BlenderSceneIR, script_path: Path | None = None):
        return validate_outputs(ir, script_path=script_path)
