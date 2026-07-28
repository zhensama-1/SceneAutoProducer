from __future__ import annotations

import argparse
import sys
from pathlib import Path

from src.scene_initialization import SceneInitializer
from src.pipeline.step2_loop import run_step2_multi_agent_loop


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate an editable Blender scene from 2D image initialization.")
    parser.add_argument("--inputs", nargs="*", default=[], help="Input image paths.")
    parser.add_argument("--demo", action="store_true", help="Run deterministic demo scene without images.")
    parser.add_argument("--scene-id", default="example_scene", help="Stable scene id used for output names.")
    parser.add_argument("--output-dir", default="outputs/example_scene", help="Output root directory.")
    parser.add_argument("--asset-metadata", default="assets/metadata/assets.json", help="Asset metadata JSON.")
    parser.add_argument("--scene-style", default="neutral", choices=["neutral", "warm"], help="Material/style hint.")
    parser.add_argument("--export", action="append", choices=["glb", "fbx", "obj"], default=[], help="Optional export format.")
    parser.add_argument("--step2-iterations", type=int, default=3, help="Maximum Step 2 multi-agent refinement iterations.")
    parser.add_argument("--run-blender", action="store_true", help="Execute generated script with Blender.")
    parser.add_argument("--blender-exe", default="blender", help="Blender executable path.")
    return parser.parse_args(argv)


def run_pipeline(args: argparse.Namespace) -> dict[str, Path]:
    output_root = Path(args.output_dir).resolve()
    init_dir = output_root / "scene_initialization"
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

    step2_outputs = run_step2_multi_agent_loop(
        initialization=initialization,
        output_root=output_root,
        asset_metadata_path=Path(args.asset_metadata).resolve(),
        scene_style=args.scene_style,
        exports=args.export,
        iterations=getattr(args, "step2_iterations", 3),
        run_blender=args.run_blender,
        blender_exe=args.blender_exe,
    )
    outputs = {
        "initialization": init_path,
    }
    outputs.update(step2_outputs)
    return outputs


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    outputs = run_pipeline(args)
    print("Generated editable Blender scene artifacts:")
    for name, path in outputs.items():
        print(f"- {name}: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
