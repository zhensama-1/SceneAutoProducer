from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

from src.asset_retrieval import AssetLibrary
from src.bpy_compiler import BlenderCodeCompiler, CodeRepairAgent
from src.scene_initialization import SceneInitializer
from src.scene_planner import ScenePlannerAgent
from src.validation import validate_outputs


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate an editable Blender scene from 2D image initialization.")
    parser.add_argument("--inputs", nargs="*", default=[], help="Input image paths.")
    parser.add_argument("--demo", action="store_true", help="Run deterministic demo scene without images.")
    parser.add_argument("--scene-id", default="example_scene", help="Stable scene id used for output names.")
    parser.add_argument("--output-dir", default="outputs/example_scene", help="Output root directory.")
    parser.add_argument("--asset-metadata", default="assets/metadata/assets.json", help="Asset metadata JSON.")
    parser.add_argument("--scene-style", default="neutral", choices=["neutral", "warm"], help="Material/style hint.")
    parser.add_argument("--export", action="append", choices=["glb", "fbx", "obj"], default=[], help="Optional export format.")
    parser.add_argument("--run-blender", action="store_true", help="Execute generated script with Blender.")
    parser.add_argument("--blender-exe", default="blender", help="Blender executable path.")
    return parser.parse_args(argv)


def run_pipeline(args: argparse.Namespace) -> dict[str, Path]:
    output_root = Path(args.output_dir).resolve()
    init_dir = output_root / "scene_initialization"
    ir_dir = output_root / "scene_ir"
    script_dir = output_root / "blender_scripts"
    report_dir = output_root / "reports"

    initializer = SceneInitializer()
    if args.demo:
        initialization = initializer.demo_initialization(args.scene_id, output_root)
    else:
        image_paths = [Path(item).resolve() for item in args.inputs]
        missing = [str(path) for path in image_paths if not path.exists()]
        if missing:
            raise FileNotFoundError(f"Input image(s) not found: {', '.join(missing)}")
        if not image_paths:
            raise ValueError("Provide --inputs or use --demo")
        initialization = initializer.initialize(image_paths, args.scene_id, output_root)

    init_path = init_dir / f"{args.scene_id}.init.json"
    initializer.write(initialization, init_path)

    asset_library = AssetLibrary.load(Path(args.asset_metadata).resolve())
    planner = ScenePlannerAgent(asset_library=asset_library, scene_style=args.scene_style)
    ir = planner.plan(initialization, output_root, exports=args.export)
    ir_path = ir_dir / f"{args.scene_id}.scene_ir.json"
    ir_path.parent.mkdir(parents=True, exist_ok=True)
    ir_path.write_text(json.dumps(ir.to_dict(), indent=2), encoding="utf-8")

    script_path = script_dir / f"{args.scene_id}.build_scene.py"
    BlenderCodeCompiler().compile(ir, script_path)

    blend_path = Path(ir.scene["output_blend"])
    if args.run_blender:
        execute_blender(args.blender_exe, script_path)
        if not blend_path.exists():
            raise RuntimeError(f"Blender finished but did not create {blend_path}")

    report = validate_outputs(ir, script_path=script_path, blend_path=blend_path if args.run_blender else None)
    report.write(
        report_dir / f"{args.scene_id}.validation.json",
        report_dir / f"{args.scene_id}.validation.md",
    )
    return {
        "initialization": init_path,
        "scene_ir": ir_path,
        "script": script_path,
        "report": report_dir / f"{args.scene_id}.validation.json",
        "blend": blend_path,
    }


def execute_blender(blender_exe: str, script_path: Path) -> None:
    executable = shutil.which(blender_exe) or blender_exe
    command = [executable, "--background", "--python", str(script_path)]
    result = subprocess.run(command, capture_output=True, text=True, check=False)
    if result.returncode == 0:
        return
    error_text = result.stderr + "\n" + result.stdout
    repaired = CodeRepairAgent().repair(script_path, error_text)
    if repaired:
        retry = subprocess.run(command, capture_output=True, text=True, check=False)
        if retry.returncode == 0:
            return
        error_text = retry.stderr + "\n" + retry.stdout
    raise RuntimeError(error_text[-4000:])


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    outputs = run_pipeline(args)
    print("Generated editable Blender scene artifacts:")
    for name, path in outputs.items():
        print(f"- {name}: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
