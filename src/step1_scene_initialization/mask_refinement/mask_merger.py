from __future__ import annotations

from src.mask_refinement.refiner import MaskRefinementAgent
from src.step1_scene_initialization.schemas import DetectedObject


class MaskMerger:
    def __init__(self):
        self.agent = MaskRefinementAgent()

    def merge_fragments(self, detections: list[DetectedObject]) -> list[DetectedObject]:
        return self.agent.refine(detections)
