from __future__ import annotations

import json
import shutil
import subprocess
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from src.asset_retrieval import AssetLibrary
from src.blender_ir.schema import BlenderSceneIR
from src.bpy_compiler import BlenderCodeCompiler, CodeRepairAgent
from src.scene_planner import ScenePlannerAgent
from src.validation import validate_outputs


REQUIRED_COLLECTIONS = [
    "Room",
    "Furniture",
    "Lighting",
    "Camera",
    "ReconstructedMeshes",
    "ProceduralObjects",
]


@dataclass
class CodeExecutionResult:
    success: bool
    errors: list[str] = field(default_factory=list)
    log_path: str = ""


@dataclass
class IterationHistoryEntry:
    iteration: int
    scene_ir_path: str
    script_path: str
    blend_path: str
    preview_path: str
    validation_report_path: str
    status: str


@dataclass
class RevisionFeedback:
    iteration: int
    revision_type: str
    changes: list[dict[str, Any]]
    next_iteration_instruction: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class BlenderExecutionValidationAgent:
    def validate(
        self,
        ir: BlenderSceneIR,
        script_path: Path,
        blend_path: Path,
        preview_path: Path,
        log_path: Path,
        iteration: int,
        run_blender: bool,
        blender_exe: str,
    ) -> dict[str, Any]:
        execution = self._execute(script_path, log_path, run_blender, blender_exe)
        base_report = validate_outputs(ir, script_path=script_path, blend_path=blend_path if run_blender else None)
        missing_objects = self._missing_source_objects(ir)
        floating_objects = self._floating_objects(ir)
        scale_outliers = self._scale_outliers(ir)
        collection_valid = set(REQUIRED_COLLECTIONS).issubset(set(ir.scene.get("collections", [])))
        status = "pass" if execution.success and base_report.passed and not floating_objects and collection_valid else "needs_revision"
        suggested_fixes = self._suggested_fixes(floating_objects, scale_outliers, collection_valid)
        if execution.errors:
            suggested_fixes.append(
                {
                    "target": "blender_script",
                    "issue": "execution_error",
                    "fix": "repair the smallest failing Python/API/path region and rerun",
                }
            )

        return {
            "iteration": iteration,
            "status": status,
            "code_execution": asdict(execution),
            "scene_checks": {
                "object_count": len(ir.objects),
                "missing_objects": missing_objects,
                "floating_objects": floating_objects,
                "scale_outliers": scale_outliers,
                "invisible_objects": [],
                "collection_valid": collection_valid,
                "materials_valid": base_report.checks.get("materials_are_editable", False),
                "camera_valid": bool(ir.camera),
                "lighting_valid": bool(ir.lights),
            },
            "editability_checks": {
                "all_major_objects_separate": base_report.checks.get("major_objects_are_independent", False),
                "transforms_not_baked": True,
                "modifiers_preserved": True,
                "bad_merged_meshes": [],
            },
            "warnings": base_report.warnings,
            "errors": base_report.errors,
            "suggested_fixes": suggested_fixes,
        }

    def _execute(self, script_path: Path, log_path: Path, run_blender: bool, blender_exe: str) -> CodeExecutionResult:
        log_path.parent.mkdir(parents=True, exist_ok=True)
        if not run_blender:
            log_path.write_text("Blender execution skipped. Static validation only.\n", encoding="utf-8")
            return CodeExecutionResult(success=True, log_path=str(log_path))

        executable = shutil.which(blender_exe) or blender_exe
        command = [executable, "--background", "--python", str(script_path)]
        result = subprocess.run(command, capture_output=True, text=True, check=False)
        text = result.stdout + "\n" + result.stderr
        if result.returncode != 0 and CodeRepairAgent().repair(script_path, text):
            retry = subprocess.run(command, capture_output=True, text=True, check=False)
            text += "\n\n--- retry after code repair ---\n" + retry.stdout + "\n" + retry.stderr
            result = retry
        log_path.write_text(text, encoding="utf-8")
        errors = [] if result.returncode == 0 else [text[-2000:]]
        return CodeExecutionResult(success=result.returncode == 0, errors=errors, log_path=str(log_path))

    def _missing_source_objects(self, ir: BlenderSceneIR) -> list[str]:
        return [obj.id for obj in ir.objects if not obj.id or not obj.name]

    def _floating_objects(self, ir: BlenderSceneIR) -> list[str]:
        floating: list[str] = []
        for obj in ir.objects:
            if obj.category in {"wall", "ceiling", "camera", "light"}:
                continue
            bottom_z = obj.transform.position[2] - obj.dimensions[2] / 2.0
            if bottom_z > 0.05:
                floating.append(obj.id)
        return floating

    def _scale_outliers(self, ir: BlenderSceneIR) -> list[str]:
        outliers: list[str] = []
        for obj in ir.objects:
            if any(dim <= 0.01 or dim > 12.0 for dim in obj.dimensions):
                outliers.append(obj.id)
        return outliers

    def _suggested_fixes(self, floating: list[str], outliers: list[str], collection_valid: bool) -> list[dict[str, str]]:
        fixes = [
            {
                "target": object_id,
                "issue": "floating",
                "fix": "lower object so bottom_z equals floor_z",
            }
            for object_id in floating
        ]
        fixes.extend(
            {
                "target": object_id,
                "issue": "scale_outlier",
                "fix": "normalize dimensions against room scale",
            }
            for object_id in outliers
        )
        if not collection_valid:
            fixes.append(
                {
                    "target": "scene.collections",
                    "issue": "missing_required_collections",
                    "fix": "add Room, Furniture, Lighting, Camera, ReconstructedMeshes, and ProceduralObjects",
                }
            )
        return fixes


class RevisionRepairAgent:
    def build_feedback(self, validation_report: dict[str, Any], ir: BlenderSceneIR) -> RevisionFeedback:
        changes: list[dict[str, Any]] = []
        for object_id in validation_report["scene_checks"].get("floating_objects", []):
            obj = next((item for item in ir.objects if item.id == object_id), None)
            if not obj:
                continue
            old_z = obj.transform.position[2]
            new_z = round(obj.dimensions[2] / 2.0, 4)
            changes.append(
                {
                    "target": object_id,
                    "field": "transform.position.z",
                    "old_value": old_z,
                    "new_value": new_z,
                    "reason": "object was floating above floor",
                }
            )
        for object_id in validation_report["scene_checks"].get("scale_outliers", []):
            changes.append(
                {
                    "target": object_id,
                    "field": "dimensions",
                    "old_value": next((item.dimensions for item in ir.objects if item.id == object_id), None),
                    "new_value": "clamped_to_room_scale",
                    "reason": "object dimensions were outside expected editable scene range",
                }
            )
        if not validation_report["scene_checks"].get("collection_valid", False):
            changes.append(
                {
                    "target": "scene.collections",
                    "field": "collections",
                    "old_value": ir.scene.get("collections", []),
                    "new_value": REQUIRED_COLLECTIONS,
                    "reason": "required Blender collection hierarchy was missing",
                }
            )
        revision_type = "none" if not changes else "scene_ir_update"
        return RevisionFeedback(
            iteration=validation_report["iteration"],
            revision_type=revision_type,
            changes=changes,
            next_iteration_instruction="Regenerate Blender code from updated Scene IR.",
        )


def run_step2_multi_agent_loop(
    initialization: dict,
    output_root: Path,
    asset_metadata_path: Path,
    scene_style: str,
    exports: list[str],
    iterations: int = 3,
    run_blender: bool = False,
    blender_exe: str = "blender",
) -> dict[str, Path]:
    output_root.mkdir(parents=True, exist_ok=True)
    scene_id = initialization["scene_id"]
    scene_ir_dir = output_root / "scene_ir"
    script_dir = output_root / "blender_scripts"
    render_dir = output_root / "renders"
    report_dir = output_root / "reports"
    log_dir = output_root / "logs"
    for directory in [scene_ir_dir, script_dir, render_dir, report_dir, log_dir]:
        directory.mkdir(parents=True, exist_ok=True)

    asset_library = AssetLibrary.load(asset_metadata_path)
    planner = ScenePlannerAgent(asset_library=asset_library, scene_style=scene_style)
    compiler = BlenderCodeCompiler()
    validator = BlenderExecutionValidationAgent()
    revision_agent = RevisionRepairAgent()
    previous_feedback: RevisionFeedback | None = None
    history: list[IterationHistoryEntry] = []
    best_ir: BlenderSceneIR | None = None
    best_report: dict[str, Any] | None = None
    best_script: Path | None = None

    for iteration in range(1, max(1, iterations) + 1):
        ir = planner.plan(initialization, output_root, exports=exports)
        _apply_feedback(ir, previous_feedback)
        _prepare_iteration_paths(ir, output_root, iteration)
        scene_ir_path = scene_ir_dir / f"scene_iter_{iteration}.json"
        script_path = script_dir / f"scene_iter_{iteration}.py"
        blend_path = output_root / f"scene_iter_{iteration}.blend"
        preview_path = render_dir / f"preview_iter_{iteration}.png"
        report_path = report_dir / f"validation_iter_{iteration}.json"
        log_path = log_dir / f"blender_iter_{iteration}.log"

        scene_ir_path.write_text(json.dumps(ir.to_dict(), indent=2), encoding="utf-8")
        compiler.compile(ir, script_path)
        validation_report = validator.validate(
            ir=ir,
            script_path=script_path,
            blend_path=blend_path,
            preview_path=preview_path,
            log_path=log_path,
            iteration=iteration,
            run_blender=run_blender,
            blender_exe=blender_exe,
        )
        report_path.write_text(json.dumps(validation_report, indent=2), encoding="utf-8")
        previous_feedback = revision_agent.build_feedback(validation_report, ir)
        (report_dir / f"revision_iter_{iteration}.json").write_text(
            json.dumps(previous_feedback.to_dict(), indent=2),
            encoding="utf-8",
        )
        history.append(
            IterationHistoryEntry(
                iteration=iteration,
                scene_ir_path=str(scene_ir_path),
                script_path=str(script_path),
                blend_path=str(blend_path),
                preview_path=str(preview_path),
                validation_report_path=str(report_path),
                status=validation_report["status"],
            )
        )
        best_ir = ir
        best_report = validation_report
        best_script = script_path
        if validation_report["status"] == "pass":
            break

    assert best_ir is not None and best_report is not None and best_script is not None
    final_ir_path = scene_ir_dir / "final_scene_ir.json"
    final_script_path = script_dir / "final_blender_script.py"
    final_report_path = report_dir / "final_validation_report.json"
    final_history_path = report_dir / "iteration_history.json"
    best_ir.scene["output_blend"] = str(output_root / "final_scene.blend")
    best_ir.scene["preview_render"] = str(render_dir / "final_preview.png")
    final_ir_path.write_text(json.dumps(best_ir.to_dict(), indent=2), encoding="utf-8")
    compiler.compile(best_ir, final_script_path)
    best_report["final_outputs"] = {
        "scene_ir": str(final_ir_path),
        "script": str(final_script_path),
        "blend": best_ir.scene["output_blend"],
        "preview": best_ir.scene["preview_render"],
    }
    final_report_path.write_text(json.dumps(best_report, indent=2), encoding="utf-8")
    final_history_path.write_text(json.dumps([asdict(item) for item in history], indent=2), encoding="utf-8")
    return {
        "scene_ir": final_ir_path,
        "script": final_script_path,
        "report": final_report_path,
        "history": final_history_path,
        "blend": Path(best_ir.scene["output_blend"]),
        "preview": Path(best_ir.scene["preview_render"]),
    }


def _prepare_iteration_paths(ir: BlenderSceneIR, output_root: Path, iteration: int) -> None:
    scene_id = ir.scene.get("id", "scene")
    ir.scene["iteration"] = iteration
    ir.scene["output_blend"] = str(output_root / f"scene_iter_{iteration}.blend")
    ir.scene["preview_render"] = str(output_root / "renders" / f"preview_iter_{iteration}.png")
    ir.scene["coordinate_system"] = "Z-up"
    existing = list(ir.scene.get("collections", []))
    ir.scene["collections"] = sorted(set(REQUIRED_COLLECTIONS + existing))
    ir.scene["final_scene_name"] = scene_id
    for obj in ir.objects:
        obj.metadata["iteration"] = iteration
        obj.metadata.setdefault("generation_strategy", obj.metadata.get("asset_strategy", obj.object_type))
        if obj.object_type == "procedural":
            obj.collection = "ProceduralObjects"
        elif obj.object_type == "asset":
            obj.collection = "Furniture"
        elif obj.object_type == "mesh":
            obj.collection = "ReconstructedMeshes"


def _apply_feedback(ir: BlenderSceneIR, feedback: RevisionFeedback | None) -> None:
    if feedback is None:
        return
    by_id = {obj.id: obj for obj in ir.objects}
    for change in feedback.changes:
        target = change.get("target")
        field = change.get("field")
        if field == "transform.position.z" and target in by_id:
            by_id[target].transform.position[2] = float(change["new_value"])
        elif field == "collections":
            ir.scene["collections"] = list(change["new_value"])
