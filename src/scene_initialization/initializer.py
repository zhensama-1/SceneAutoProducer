from __future__ import annotations

import json
import base64
from pathlib import Path

from src.mask_refinement import MaskRefinementAgent
from src.mesh_reconstruction import BaseMeshReconstructor, PlaceholderMeshReconstructor

from .detectors import BaseObjectDetector, HeuristicObjectDetector
from .types import SceneInitializationObject, scene_initialization_to_dict


class SceneInitializer:
    def __init__(
        self,
        detector: BaseObjectDetector | None = None,
        refiner: MaskRefinementAgent | None = None,
        reconstructor: BaseMeshReconstructor | None = None,
    ):
        self.detector = detector or HeuristicObjectDetector()
        self.refiner = refiner or MaskRefinementAgent()
        self.reconstructor = reconstructor or PlaceholderMeshReconstructor()

    def initialize(self, image_paths: list[Path], scene_id: str, output_root: Path) -> dict:
        mask_dir = output_root / "masks"
        recon_dir = output_root / "recon"
        all_objects: list[SceneInitializationObject] = []
        for image_index, image_path in enumerate(image_paths):
            detections = self.detector.detect(image_path, mask_dir)
            refined = self.refiner.refine(detections)
            for object_index, detected in enumerate(refined, start=1):
                object_id = self._stable_object_id(detected.category, image_index, object_index)
                mesh_path = self.reconstructor.reconstruct(detected, recon_dir)
                position, scale = self._estimate_transform(detected.bbox_2d)
                all_objects.append(
                    SceneInitializationObject(
                        id=object_id,
                        category=detected.category,
                        mask_path=str(detected.mask_path or ""),
                        mesh_path=str(mesh_path),
                        bbox_2d=detected.bbox_2d,
                        position=position,
                        rotation_euler=[0.0, 0.0, 0.0],
                        scale=scale,
                        confidence=detected.confidence,
                    )
                )
        return scene_initialization_to_dict(scene_id, all_objects)

    def write(self, initialization: dict, output_path: Path) -> Path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(initialization, indent=2), encoding="utf-8")
        return output_path

    def demo_initialization(self, scene_id: str, output_root: Path) -> dict:
        recon_dir = output_root / "recon"
        recon_dir.mkdir(parents=True, exist_ok=True)
        mask_dir = output_root / "masks"
        mask_dir.mkdir(parents=True, exist_ok=True)
        demo_objects = [
            ("table_01", "table", [210, 250, 470, 390], [0.0, 0.0, 0.38], [1.5, 0.8, 0.75], 0.91),
            ("chair_01", "chair", [110, 255, 220, 440], [-0.95, -0.1, 0.45], [0.55, 0.55, 0.9], 0.84),
            ("cabinet_01", "cabinet", [510, 180, 690, 430], [1.65, 0.18, 0.75], [0.9, 0.45, 1.5], 0.82),
        ]
        objects: list[SceneInitializationObject] = []
        placeholder = PlaceholderMeshReconstructor()
        for object_id, category, bbox, position, scale, confidence in demo_objects:
            detected = self._demo_detected_object(object_id, category, bbox, confidence, mask_dir)
            mesh_path = placeholder.reconstruct(detected, recon_dir)
            objects.append(
                SceneInitializationObject(
                    id=object_id,
                    category=category,
                    mask_path=str(detected.mask_path),
                    mesh_path=str(mesh_path),
                    bbox_2d=bbox,
                    position=position,
                    rotation_euler=[0.0, 0.0, 0.0],
                    scale=scale,
                    confidence=confidence,
                )
            )
        return scene_initialization_to_dict(scene_id, objects)

    def _stable_object_id(self, category: str, image_index: int, object_index: int) -> str:
        clean = "".join(ch if ch.isalnum() else "_" for ch in category.lower()).strip("_") or "object"
        return f"{clean}_{image_index + 1:02d}_{object_index:02d}"

    def _estimate_transform(self, bbox: list[int]) -> tuple[list[float], list[float]]:
        x1, y1, x2, y2 = bbox
        width = max(1, x2 - x1)
        height = max(1, y2 - y1)
        center_x = (x1 + x2) / 2.0
        normalized_x = (center_x - 320.0) / 180.0
        scene_height = max(0.25, height / 240.0)
        scene_width = max(0.25, width / 260.0)
        return [normalized_x, 0.0, scene_height / 2.0], [scene_width, max(0.25, scene_width * 0.55), scene_height]

    def _demo_detected_object(self, object_id: str, category: str, bbox: list[int], confidence: float, mask_dir: Path):
        from .types import DetectedObject

        mask_path = mask_dir / f"{object_id}.png"
        mask_path.write_bytes(
            base64.b64decode(
                "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADElEQVR42mP8z8BQDwAFgwJ/lG6YvQAAAABJRU5ErkJggg=="
            )
        )
        return DetectedObject(
            id=object_id,
            category=category,
            bbox_2d=bbox,
            confidence=confidence,
            mask_path=str(mask_path),
            image_path=None,
        )
