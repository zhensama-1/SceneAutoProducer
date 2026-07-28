from __future__ import annotations

from pathlib import Path

from src.pipeline.step2_loop import run_step2_multi_agent_loop


class Step2BlenderGenerationOrchestrator:
    def run(
        self,
        initialization: dict,
        output_root: Path,
        asset_metadata_path: Path,
        scene_style: str = "neutral",
        exports: list[str] | None = None,
        iterations: int = 3,
        run_blender: bool = False,
        blender_exe: str = "blender",
    ) -> dict[str, Path]:
        return run_step2_multi_agent_loop(
            initialization=initialization,
            output_root=output_root,
            asset_metadata_path=asset_metadata_path,
            scene_style=scene_style,
            exports=exports or [],
            iterations=iterations,
            run_blender=run_blender,
            blender_exe=blender_exe,
        )
