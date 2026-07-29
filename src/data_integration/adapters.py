from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from src.blender_ir.schema import BlenderSceneIR, CameraIR, MaterialIR, ObjectIR, Transform
from src.data_integration.categories import CategoryRegistry
from src.data_integration.manifest import DataManifest, ManifestRecord


def _relative(path: Path, root: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return path.resolve().as_posix()


def _first_existing(directory: Path, names: tuple[str, ...]) -> Path | None:
    for name in names:
        candidate = directory / name
        if candidate.exists():
            return candidate
    return None


class InfinigenIndoorsAdapter:
    REQUIRED = ("rgb", "instance_mask", "depth", "camera", "layout")

    def __init__(self, categories: CategoryRegistry):
        self.categories = categories

    def discover(self, raw_root: Path, output_root: Path, split: str) -> DataManifest:
        records: list[ManifestRecord] = []
        for scene_dir in sorted(path for path in raw_root.iterdir() if path.is_dir()):
            paths = {
                "rgb": _first_existing(scene_dir, ("rgb.png", "image.png", "Image.png")),
                "instance_mask": _first_existing(scene_dir, ("instance_mask.png", "instances.png")),
                "semantic_mask": _first_existing(scene_dir, ("semantic_mask.png", "semantic.png")),
                "depth": _first_existing(scene_dir, ("depth.exr", "depth.npy", "depth.png")),
                "camera": _first_existing(scene_dir, ("cameras.json", "camera.json")),
                "layout": _first_existing(scene_dir, ("layout.json", "objects.json")),
                "native_scene": _first_existing(scene_dir, ("native_scene.json", "scene.json")),
                "blend": _first_existing(scene_dir, ("scene.blend",)),
            }
            missing = [name for name in self.REQUIRED if paths.get(name) is None]
            if missing:
                raise ValueError(f"{scene_dir.name}: missing Infinigen modalities: {', '.join(missing)}")
            ir_path = output_root / "scene_ir" / f"{scene_dir.name}.scene_ir.json"
            self.convert_scene_ir(scene_dir.name, paths["camera"], paths["layout"], ir_path)
            modalities = {
                key: _relative(value, output_root.parent.parent.parent)
                for key, value in paths.items()
                if value is not None
            }
            modalities["scene_ir"] = _relative(ir_path, output_root.parent.parent.parent)
            records.append(
                ManifestRecord(
                    sample_id=scene_dir.name,
                    source="infinigen_indoors",
                    split=split,
                    modalities=modalities,
                    metadata={"unit": "meter", "coordinate_system": "Z-up"},
                )
            )
        return DataManifest(source="infinigen_indoors", records=records)

    def convert_scene_ir(self, scene_id: str, camera_path: Path, layout_path: Path, output: Path) -> None:
        camera_data = json.loads(camera_path.read_text(encoding="utf-8"))
        if isinstance(camera_data, list):
            camera_data = camera_data[0] if camera_data else {}
        width = float(camera_data.get("width", 640))
        fx = float(camera_data.get("fx", camera_data.get("focal_length_px", 700)))
        sensor_width = float(camera_data.get("sensor_width", 32.0))
        camera = CameraIR(
            name=str(camera_data.get("name", "camera_main")),
            position=[float(v) for v in camera_data.get("position", [0, -3, 1.6])],
            rotation_euler=[float(v) for v in camera_data.get("rotation_euler", [1.5708, 0, 0])],
            focal_length=float(camera_data.get("focal_length", fx * sensor_width / width)),
            sensor_width=sensor_width,
        )
        layout_data = json.loads(layout_path.read_text(encoding="utf-8"))
        items = layout_data.get("objects", layout_data if isinstance(layout_data, list) else [])
        objects: list[ObjectIR] = []
        for index, item in enumerate(items):
            object_id = str(item.get("id", f"object_{index:04d}"))
            dimensions = item.get("dimensions", item.get("size", [1, 1, 1]))
            objects.append(
                ObjectIR(
                    id=object_id,
                    name=str(item.get("name", object_id)),
                    category=self.categories.normalize(str(item.get("category", item.get("label", "")))),
                    collection=str(item.get("collection", "Furniture")),
                    object_type="ground_truth",
                    transform=Transform.from_dict(
                        {
                            "position": item.get("position", item.get("center", [0, 0, 0])),
                            "rotation_euler": item.get("rotation_euler", [0, 0, 0]),
                            "scale": item.get("scale", [1, 1, 1]),
                        }
                    ),
                    dimensions=[float(v) for v in dimensions],
                    material_id="infinigen_default",
                    metadata={
                        "source": "infinigen_indoors",
                        "instance_id": item.get("instance_id", object_id),
                    },
                )
            )
        ir = BlenderSceneIR(
            scene={
                "id": scene_id,
                "unit": "meter",
                "coordinate_system": "Z-up",
                "output_blend": f"outputs/{scene_id}/ground_truth.blend",
                "collections": ["Room", "Furniture", "Lighting", "Camera"],
            },
            objects=objects,
            materials=[MaterialIR(id="infinigen_default", name="Infinigen default")],
            camera=camera,
        )
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(ir.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")


class DeepFurnitureAdapter:
    def __init__(self, categories: CategoryRegistry):
        self.categories = categories

    def convert(self, annotation_path: Path, image_root: Path, split: str) -> DataManifest:
        data = json.loads(annotation_path.read_text(encoding="utf-8"))
        categories = {
            int(item["id"]): self.categories.normalize(str(item["name"]))
            for item in data.get("categories", [])
        }
        annotations_by_image: dict[int, list[dict[str, Any]]] = {}
        for annotation in data.get("annotations", []):
            normalized = dict(annotation)
            normalized["canonical_category"] = categories.get(
                int(annotation.get("category_id", -1)), "unknown"
            )
            annotations_by_image.setdefault(int(annotation["image_id"]), []).append(normalized)
        records = []
        for image in data.get("images", []):
            image_id = int(image["id"])
            records.append(
                ManifestRecord(
                    sample_id=f"deepfurniture:{image_id}",
                    source="deepfurniture",
                    split=split,
                    modalities={"rgb": (image_root / str(image["file_name"])).as_posix()},
                    metadata={
                        "width": image.get("width"),
                        "height": image.get("height"),
                        "annotations": annotations_by_image.get(image_id, []),
                    },
                )
            )
        return DataManifest(source="deepfurniture", records=records)


class RealValidationAdapter:
    def build(
        self,
        source: str,
        image_root: Path,
        annotation_path: Path | None,
        depth_root: Path | None = None,
    ) -> DataManifest:
        annotation_data: dict[str, Any] = {}
        if annotation_path and annotation_path.exists():
            raw = json.loads(annotation_path.read_text(encoding="utf-8"))
            annotation_data = raw.get("samples", raw)
        records: list[ManifestRecord] = []
        for image_path in sorted(
            path for path in image_root.rglob("*") if path.suffix.casefold() in {".jpg", ".jpeg", ".png"}
        ):
            sample_id = image_path.stem
            modalities = {"rgb": image_path.as_posix()}
            if depth_root:
                for suffix in (".png", ".npy", ".exr"):
                    depth = depth_root / f"{sample_id}{suffix}"
                    if depth.exists():
                        modalities["depth"] = depth.as_posix()
                        break
            records.append(
                ManifestRecord(
                    sample_id=f"{source}:{sample_id}",
                    source=source,
                    split="real_val",
                    modalities=modalities,
                    metadata=dict(annotation_data.get(sample_id, {})),
                )
            )
        return DataManifest(
            source=source,
            records=records,
            metadata={"training_allowed": False, "domain": "real"},
        )
