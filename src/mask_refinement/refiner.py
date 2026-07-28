from __future__ import annotations

from src.scene_initialization.types import DetectedObject


def _area(bbox: list[int]) -> int:
    return max(0, bbox[2] - bbox[0]) * max(0, bbox[3] - bbox[1])


def _iou(a: list[int], b: list[int]) -> float:
    x1 = max(a[0], b[0])
    y1 = max(a[1], b[1])
    x2 = min(a[2], b[2])
    y2 = min(a[3], b[3])
    inter = _area([x1, y1, x2, y2])
    union = _area(a) + _area(b) - inter
    return 0.0 if union <= 0 else inter / union


def _merge_bbox(a: list[int], b: list[int]) -> list[int]:
    return [min(a[0], b[0]), min(a[1], b[1]), max(a[2], b[2]), max(a[3], b[3])]


class MaskRefinementAgent:
    """Rule-based refinement layer around model masks.

    Model-backed refiners can replace this class. The public contract stays the same:
    return one refined object record per semantic object.
    """

    def __init__(self, duplicate_iou: float = 0.86, fragment_iou: float = 0.20, min_confidence: float = 0.15):
        self.duplicate_iou = duplicate_iou
        self.fragment_iou = fragment_iou
        self.min_confidence = min_confidence

    def refine(self, detections: list[DetectedObject]) -> list[DetectedObject]:
        candidates = [item for item in detections if item.confidence >= self.min_confidence and _area(item.bbox_2d) > 0]
        candidates.sort(key=lambda item: item.confidence, reverse=True)
        refined: list[DetectedObject] = []
        for candidate in candidates:
            match_index = self._find_merge_candidate(candidate, refined)
            if match_index is None:
                refined.append(candidate)
                continue
            existing = refined[match_index]
            merged_bbox = _merge_bbox(existing.bbox_2d, candidate.bbox_2d)
            refined[match_index] = DetectedObject(
                id=existing.id,
                category=existing.category,
                bbox_2d=merged_bbox,
                confidence=max(existing.confidence, candidate.confidence),
                mask_path=existing.mask_path or candidate.mask_path,
                image_path=existing.image_path or candidate.image_path,
            )
        return refined

    def _find_merge_candidate(self, candidate: DetectedObject, refined: list[DetectedObject]) -> int | None:
        for index, existing in enumerate(refined):
            overlap = _iou(candidate.bbox_2d, existing.bbox_2d)
            same_category = candidate.category == existing.category
            if overlap >= self.duplicate_iou:
                return index
            if same_category and overlap >= self.fragment_iou:
                return index
        return None
