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
    data_sources_config: str = "configs/data_sources.json"
    category_map: str = "configs/categories.json"
    dataset_manifest: str | None = None
    real_validation_manifest: str | None = None
    asset_sources: list[str] = field(default_factory=lambda: ["abo", "objaverse_oa"])
    asset_license_allowlist: list[str] = field(
        default_factory=lambda: ["CC0-1.0", "CC-BY-4.0"]
    )
