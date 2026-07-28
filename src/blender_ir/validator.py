from __future__ import annotations

from dataclasses import dataclass

from .schema import BlenderSceneIR


@dataclass
class ValidationError(Exception):
    message: str

    def __str__(self) -> str:
        return self.message


def validate_scene_ir(ir: BlenderSceneIR) -> list[str]:
    warnings: list[str] = []
    if not ir.scene.get("id"):
        raise ValidationError("scene.id is required")
    if not ir.scene.get("unit"):
        raise ValidationError("scene.unit is required")
    if not ir.scene.get("output_blend"):
        raise ValidationError("scene.output_blend is required")
    if not ir.objects:
        raise ValidationError("At least one object is required")
    if not ir.materials:
        raise ValidationError("At least one material is required")

    material_ids = {material.id for material in ir.materials}
    object_ids: set[str] = set()
    for obj in ir.objects:
        if obj.id in object_ids:
            raise ValidationError(f"Duplicate object id: {obj.id}")
        object_ids.add(obj.id)
        if obj.material_id not in material_ids:
            raise ValidationError(f"Object {obj.id} references missing material {obj.material_id}")
        if obj.object_type not in {"mesh", "primitive", "asset", "procedural"}:
            raise ValidationError(f"Object {obj.id} has unsupported object_type {obj.object_type}")
        if any(dim <= 0 for dim in obj.dimensions):
            raise ValidationError(f"Object {obj.id} dimensions must be positive")
        if obj.object_type == "mesh" and not obj.source_path:
            warnings.append(f"{obj.id}: mesh object has no source_path and will become a placeholder")
        if obj.object_type == "asset" and not obj.asset:
            warnings.append(f"{obj.id}: asset object has no asset metadata and will become a placeholder")
        if obj.object_type == "procedural" and not obj.procedural:
            raise ValidationError(f"{obj.id}: procedural object requires procedural spec")

    for relation in ir.relations:
        if relation.subject not in object_ids:
            warnings.append(f"Relation subject {relation.subject} is missing from objects")
        if relation.target != "world" and relation.target not in object_ids:
            warnings.append(f"Relation target {relation.target} is missing from objects")

    for constraint in ir.constraints:
        if constraint.object_id not in object_ids:
            warnings.append(f"Constraint references missing object {constraint.object_id}")
    return warnings
