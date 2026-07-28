from __future__ import annotations

from pathlib import Path

from src.scene_initialization.detectors import HeuristicObjectDetector
from src.step1_scene_initialization.schemas import DetectedObject


class GroundedSAMRunner:
    """Adapter boundary for a future Grounded-SAM implementation."""

    def __init__(self):
        self.fallback = HeuristicObjectDetector()

    def run(self, image_path: Path, output_mask_dir: Path) -> list[DetectedObject]:
        return self.fallback.detect(image_path, output_mask_dir)
