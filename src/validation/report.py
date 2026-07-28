from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path

from src.blender_ir.schema import BlenderSceneIR
from src.blender_ir.validator import validate_scene_ir


@dataclass
class ValidationReport:
    scene_id: str
    passed: bool
    checks: dict[str, bool]
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    output_files: dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return asdict(self)

    def write(self, json_path: Path, markdown_path: Path | None = None) -> None:
        json_path.parent.mkdir(parents=True, exist_ok=True)
        json_path.write_text(json.dumps(self.to_dict(), indent=2), encoding="utf-8")
        if markdown_path:
            markdown_path.parent.mkdir(parents=True, exist_ok=True)
            lines = [
                f"# Validation Report: {self.scene_id}",
                "",
                f"Passed: {self.passed}",
                "",
                "## Checks",
            ]
            lines.extend(f"- [{'x' if passed else ' '}] {name}" for name, passed in self.checks.items())
            if self.warnings:
                lines.extend(["", "## Warnings"])
                lines.extend(f"- {warning}" for warning in self.warnings)
            if self.errors:
                lines.extend(["", "## Errors"])
                lines.extend(f"- {error}" for error in self.errors)
            markdown_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def validate_outputs(ir: BlenderSceneIR, script_path: Path | None = None, blend_path: Path | None = None) -> ValidationReport:
    warnings: list[str] = []
    errors: list[str] = []
    try:
        warnings.extend(validate_scene_ir(ir))
    except Exception as exc:
        errors.append(str(exc))

    object_ids = [obj.id for obj in ir.objects]
    checks = {
        "major_objects_are_independent": len(object_ids) == len(set(object_ids)) and len(object_ids) > 0,
        "collections_are_named": all(bool(obj.collection) for obj in ir.objects),
        "materials_are_editable": all(obj.material_id for obj in ir.objects) and bool(ir.materials),
        "grounded_constraints_exist": any(item.kind == "grounded" for item in ir.constraints),
        "architecture_is_procedural": all(
            obj.object_type == "procedural" for obj in ir.objects if obj.category in {"floor", "wall", "door", "window"}
        ),
        "script_is_generated": script_path is not None and script_path.exists(),
        "blend_output_declared": bool(ir.scene.get("output_blend")),
    }
    if blend_path is not None:
        checks["blend_file_exists"] = blend_path.exists()
    for obj in ir.objects:
        if obj.category not in {"floor", "wall", "ceiling", "window"} and obj.transform.position[2] < 0:
            warnings.append(f"{obj.id} has a negative z position")
        if obj.object_type == "mesh" and obj.metadata.get("asset_strategy") == "keep_reconstructed_mesh":
            warnings.append(f"{obj.id} keeps reconstructed mesh; inspect editability manually")

    passed = not errors and all(checks.values())
    return ValidationReport(
        scene_id=str(ir.scene.get("id", "scene")),
        passed=passed,
        checks=checks,
        warnings=warnings,
        errors=errors,
        output_files={
            "script": str(script_path) if script_path else "",
            "blend": str(blend_path or ir.scene.get("output_blend", "")),
            "preview": str(ir.scene.get("preview_render", "")),
        },
    )
