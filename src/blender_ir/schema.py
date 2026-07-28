from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


Vector3 = list[float]


def _vec3(value: Any, default: Vector3 | None = None) -> Vector3:
    if value is None:
        return list(default or [0.0, 0.0, 0.0])
    if len(value) != 3:
        raise ValueError(f"Expected vector length 3, got {value!r}")
    return [float(v) for v in value]


@dataclass
class Transform:
    position: Vector3 = field(default_factory=lambda: [0.0, 0.0, 0.0])
    rotation_euler: Vector3 = field(default_factory=lambda: [0.0, 0.0, 0.0])
    scale: Vector3 = field(default_factory=lambda: [1.0, 1.0, 1.0])

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> "Transform":
        data = data or {}
        return cls(
            position=_vec3(data.get("position"), [0.0, 0.0, 0.0]),
            rotation_euler=_vec3(data.get("rotation_euler"), [0.0, 0.0, 0.0]),
            scale=_vec3(data.get("scale"), [1.0, 1.0, 1.0]),
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class MaterialIR:
    id: str
    name: str
    base_color: list[float] = field(default_factory=lambda: [0.8, 0.8, 0.8, 1.0])
    roughness: float = 0.55
    metallic: float = 0.0
    alpha: float = 1.0
    texture_path: str | None = None
    normal_map_path: str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "MaterialIR":
        return cls(
            id=str(data["id"]),
            name=str(data.get("name", data["id"])),
            base_color=[float(v) for v in data.get("base_color", [0.8, 0.8, 0.8, 1.0])],
            roughness=float(data.get("roughness", 0.55)),
            metallic=float(data.get("metallic", 0.0)),
            alpha=float(data.get("alpha", 1.0)),
            texture_path=data.get("texture_path"),
            normal_map_path=data.get("normal_map_path"),
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ObjectIR:
    id: str
    name: str
    category: str
    collection: str
    object_type: str
    transform: Transform
    dimensions: Vector3
    material_id: str
    source_path: str | None = None
    primitive: dict[str, Any] | None = None
    asset: dict[str, Any] | None = None
    procedural: dict[str, Any] | None = None
    editable_parts: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ObjectIR":
        return cls(
            id=str(data["id"]),
            name=str(data.get("name", data["id"])),
            category=str(data.get("category", "unknown")),
            collection=str(data.get("collection", "Scene")),
            object_type=str(data.get("object_type", "primitive")),
            transform=Transform.from_dict(data.get("transform")),
            dimensions=_vec3(data.get("dimensions"), [1.0, 1.0, 1.0]),
            material_id=str(data.get("material_id", "default_mat")),
            source_path=data.get("source_path"),
            primitive=data.get("primitive"),
            asset=data.get("asset"),
            procedural=data.get("procedural"),
            editable_parts=list(data.get("editable_parts", [])),
            metadata=dict(data.get("metadata", {})),
        )

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["transform"] = self.transform.to_dict()
        return data


@dataclass
class RelationIR:
    subject: str
    relation: str
    target: str
    confidence: float = 1.0

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "RelationIR":
        return cls(
            subject=str(data["subject"]),
            relation=str(data["relation"]),
            target=str(data["target"]),
            confidence=float(data.get("confidence", 1.0)),
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class CameraIR:
    name: str = "camera_main"
    position: Vector3 = field(default_factory=lambda: [3.5, -5.0, 2.4])
    rotation_euler: Vector3 = field(default_factory=lambda: [1.15, 0.0, 0.62])
    focal_length: float = 35.0
    sensor_width: float = 32.0

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> "CameraIR":
        data = data or {}
        return cls(
            name=str(data.get("name", "camera_main")),
            position=_vec3(data.get("position"), [3.5, -5.0, 2.4]),
            rotation_euler=_vec3(data.get("rotation_euler"), [1.15, 0.0, 0.62]),
            focal_length=float(data.get("focal_length", 35.0)),
            sensor_width=float(data.get("sensor_width", 32.0)),
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class LightIR:
    name: str
    light_type: str
    position: Vector3
    rotation_euler: Vector3 = field(default_factory=lambda: [0.0, 0.0, 0.0])
    energy: float = 400.0
    size: float = 3.0

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "LightIR":
        return cls(
            name=str(data.get("name", "light")),
            light_type=str(data.get("light_type", "AREA")),
            position=_vec3(data.get("position"), [0.0, -3.0, 4.0]),
            rotation_euler=_vec3(data.get("rotation_euler"), [0.0, 0.0, 0.0]),
            energy=float(data.get("energy", 400.0)),
            size=float(data.get("size", 3.0)),
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ConstraintIR:
    object_id: str
    kind: str
    target: str | None = None
    parameters: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ConstraintIR":
        return cls(
            object_id=str(data["object_id"]),
            kind=str(data["kind"]),
            target=data.get("target"),
            parameters=dict(data.get("parameters", {})),
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class BlenderSceneIR:
    scene: dict[str, Any]
    objects: list[ObjectIR]
    materials: list[MaterialIR]
    relations: list[RelationIR] = field(default_factory=list)
    camera: CameraIR = field(default_factory=CameraIR)
    lights: list[LightIR] = field(default_factory=list)
    constraints: list[ConstraintIR] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "BlenderSceneIR":
        return cls(
            scene=dict(data.get("scene", {})),
            objects=[ObjectIR.from_dict(item) for item in data.get("objects", [])],
            materials=[MaterialIR.from_dict(item) for item in data.get("materials", [])],
            relations=[RelationIR.from_dict(item) for item in data.get("relations", [])],
            camera=CameraIR.from_dict(data.get("camera")),
            lights=[LightIR.from_dict(item) for item in data.get("lights", [])],
            constraints=[ConstraintIR.from_dict(item) for item in data.get("constraints", [])],
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "scene": self.scene,
            "objects": [item.to_dict() for item in self.objects],
            "materials": [item.to_dict() for item in self.materials],
            "relations": [item.to_dict() for item in self.relations],
            "camera": self.camera.to_dict(),
            "lights": [item.to_dict() for item in self.lights],
            "constraints": [item.to_dict() for item in self.constraints],
        }


BLENDER_SCENE_IR_SCHEMA: dict[str, Any] = {
    "type": "object",
    "required": ["scene", "objects", "materials", "camera", "lights"],
    "properties": {
        "scene": {
            "type": "object",
            "required": ["id", "unit", "output_blend"],
            "properties": {
                "id": {"type": "string"},
                "unit": {"type": "string"},
                "output_blend": {"type": "string"},
                "exports": {"type": "array", "items": {"type": "string"}},
            },
        },
        "objects": {"type": "array"},
        "materials": {"type": "array"},
        "relations": {"type": "array"},
        "camera": {"type": "object"},
        "lights": {"type": "array"},
        "constraints": {"type": "array"},
    },
}
