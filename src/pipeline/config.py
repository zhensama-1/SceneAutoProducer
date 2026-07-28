from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class PipelineConfig:
    scene_id: str = "example_scene"
    output_dir: str = "outputs/example_scene"
    asset_metadata: str = "assets/metadata/assets.json"
    scene_style: str = "neutral"
    step2_iterations: int = 3
    exports: list[str] = field(default_factory=list)
    run_blender: bool = False
    blender_exe: str = "blender"
