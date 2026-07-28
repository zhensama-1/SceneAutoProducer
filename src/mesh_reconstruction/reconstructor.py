from __future__ import annotations

from pathlib import Path

from src.scene_initialization.types import DetectedObject


class BaseMeshReconstructor:
    """Adapter boundary for SAM3D, TripoSR, Zero123++, or other single-object reconstruction."""

    def reconstruct(self, detected_object: DetectedObject, output_dir: Path) -> Path:
        raise NotImplementedError


class PlaceholderMeshReconstructor(BaseMeshReconstructor):
    """Writes a simple cube OBJ as a coarse stand-in mesh."""

    def reconstruct(self, detected_object: DetectedObject, output_dir: Path) -> Path:
        output_dir.mkdir(parents=True, exist_ok=True)
        obj_path = output_dir / f"{detected_object.id}.obj"
        width = max(0.25, (detected_object.bbox_2d[2] - detected_object.bbox_2d[0]) / 480.0)
        height = max(0.25, (detected_object.bbox_2d[3] - detected_object.bbox_2d[1]) / 480.0)
        depth = max(0.25, min(width, height) * 0.55)
        self._write_box_obj(obj_path, width, depth, height)
        return obj_path

    def _write_box_obj(self, path: Path, width: float, depth: float, height: float) -> None:
        x = width / 2
        y = depth / 2
        z = height / 2
        vertices = [
            (-x, -y, -z),
            (x, -y, -z),
            (x, y, -z),
            (-x, y, -z),
            (-x, -y, z),
            (x, -y, z),
            (x, y, z),
            (-x, y, z),
        ]
        faces = [
            (1, 2, 3, 4),
            (5, 8, 7, 6),
            (1, 5, 6, 2),
            (2, 6, 7, 3),
            (3, 7, 8, 4),
            (4, 8, 5, 1),
        ]
        lines = ["# placeholder coarse mesh"]
        lines.extend(f"v {vx:.6f} {vy:.6f} {vz:.6f}" for vx, vy, vz in vertices)
        lines.extend("f " + " ".join(str(index) for index in face) for face in faces)
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
