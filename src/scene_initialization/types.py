from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass
class DetectedObject:
    id: str
    category: str
    bbox_2d: list[int]
    confidence: float
    mask_path: str | None = None
    image_path: str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "DetectedObject":
        return cls(
            id=str(data["id"]),
            category=str(data.get("category", "object")),
            bbox_2d=[int(v) for v in data.get("bbox_2d", [0, 0, 1, 1])],
            confidence=float(data.get("confidence", 0.5)),
            mask_path=data.get("mask_path"),
            image_path=data.get("image_path"),
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class SceneInitializationObject:
    id: str
    category: str
    mask_path: str
    mesh_path: str
    bbox_2d: list[int]
    position: list[float]
    rotation_euler: list[float]
    scale: list[float]
    confidence: float

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def scene_initialization_to_dict(scene_id: str, objects: list[SceneInitializationObject]) -> dict[str, Any]:
    return {
        "scene_id": scene_id,
        "unit": "meters",
        "objects": [obj.to_dict() for obj in objects],
    }
