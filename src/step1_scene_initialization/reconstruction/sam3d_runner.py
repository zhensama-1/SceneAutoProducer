from __future__ import annotations

from pathlib import Path

from src.mesh_reconstruction.reconstructor import PlaceholderMeshReconstructor
from src.step1_scene_initialization.schemas import DetectedObject


class SAM3DRunner:
    """Adapter boundary for SAM3D or another single-object reconstruction model."""

    def __init__(self):
        self.fallback = PlaceholderMeshReconstructor()

    def reconstruct(self, detected_object: DetectedObject, output_dir: Path) -> Path:
        return self.fallback.reconstruct(detected_object, output_dir)
