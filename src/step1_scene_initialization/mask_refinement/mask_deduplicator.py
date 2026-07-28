from __future__ import annotations

from src.mask_refinement.refiner import MaskRefinementAgent
from src.step1_scene_initialization.schemas import DetectedObject


class MaskDeduplicator:
    def __init__(self):
        self.agent = MaskRefinementAgent()

    def remove_duplicates(self, detections: list[DetectedObject]) -> list[DetectedObject]:
        return self.agent.refine(detections)
