from __future__ import annotations

import argparse
import json
import subprocess
import sys
from dataclasses import asdict
from pathlib import Path

from src.data_integration.adapters import (
    DeepFurnitureAdapter,
    InfinigenIndoorsAdapter,
    RealValidationAdapter,
)
from src.data_integration.assets import AssetCatalogBuilder, AssetPolicy
from src.data_integration.categories import CategoryRegistry
from src.data_integration.validation import DataIntegrityValidator


def _categories(args: argparse.Namespace) -> CategoryRegistry:
    return CategoryRegistry.load(Path(args.categories))


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Integrate datasets and licensed GLB assets.")
    parser.add_argument("--categories", default="configs/categories.json")
    subparsers = parser.add_subparsers(dest="command", required=True)

    assets = subparsers.add_parser("build-assets", help="Gate, deduplicate and merge ABO/Objaverse metadata.")
    assets.add_argument("--abo", type=Path)
    assets.add_argument("--objaverse-oa", type=Path)
    assets.add_argument("--output", type=Path, default=Path("assets/metadata/assets.json"))
    assets.add_argument("--quarantine-report", type=Path, default=Path("assets/metadata/quarantine.json"))
    assets.add_argument("--allow-license", action="append", default=["CC0-1.0", "CC-BY-4.0"])
    assets.add_argument("--metadata-only", action="store_true", help="Skip local GLB existence/header checks.")

    normalize = subparsers.add_parser("normalize-glb", help="Normalize one GLB through Blender.")
    normalize.add_argument("--input", type=Path, required=True)
    normalize.add_argument("--output", type=Path, required=True)
    normalize.add_argument("--source-up", default="Z", choices=["X", "-X", "Y", "-Y", "Z", "-Z"])
    normalize.add_argument("--source-front", default="-Y", choices=["X", "-X", "Y", "-Y", "Z", "-Z"])
    normalize.add_argument("--unit-scale", type=float, default=1.0)
    normalize.add_argument("--blender-exe", default="blender")

    infinigen = subparsers.add_parser("convert-infinigen")
    infinigen.add_argument("--raw-root", type=Path, required=True)
    infinigen.add_argument("--output-root", type=Path, default=Path("data/processed/infinigen_indoors"))
    infinigen.add_argument("--split", default="train")

    deep = subparsers.add_parser("convert-deepfurniture")
    deep.add_argument("--annotations", type=Path, required=True)
    deep.add_argument("--image-root", type=Path, required=True)
    deep.add_argument("--output", type=Path, required=True)
    deep.add_argument("--split", default="train")

    real = subparsers.add_parser("build-real-validation")
    real.add_argument("--source", choices=["nyuv2", "custom"], required=True)
    real.add_argument("--image-root", type=Path, required=True)
    real.add_argument("--depth-root", type=Path)
    real.add_argument("--annotations", type=Path)
    real.add_argument("--output", type=Path, required=True)

    validate = subparsers.add_parser("validate")
    validate.add_argument("--manifest", action="append", type=Path, default=[])
    validate.add_argument("--asset-metadata", type=Path)
    validate.add_argument("--allow-license", action="append", default=["CC0-1.0", "CC-BY-4.0"])
    validate.add_argument("--metadata-only", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if args.command == "build-assets":
        sources = [(name, path) for name, path in (("abo", args.abo), ("objaverse_oa", args.objaverse_oa)) if path]
        if not sources:
            raise ValueError("Provide --abo and/or --objaverse-oa metadata")
        builder = AssetCatalogBuilder(
            _categories(args),
            AssetPolicy(set(args.allow_license)),
        )
        accepted, rejected = builder.build(sources, check_files=not args.metadata_only)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(
            json.dumps({"version": 1, "assets": [item.to_dict() for item in accepted]}, indent=2),
            encoding="utf-8",
        )
        args.quarantine_report.parent.mkdir(parents=True, exist_ok=True)
        args.quarantine_report.write_text(json.dumps({"rejected": rejected}, indent=2), encoding="utf-8")
        print(f"accepted={len(accepted)} rejected={len(rejected)}")
        return 0
    if args.command == "normalize-glb":
        source = args.input.resolve()
        output = args.output.resolve()
        if source == output:
            raise ValueError("--output must not overwrite the original GLB")
        script = Path(__file__).with_name("blender_normalize.py").resolve()
        completed = subprocess.run(
            [
                args.blender_exe,
                "--background",
                "--factory-startup",
                "--python",
                str(script),
                "--",
                "--input",
                str(source),
                "--output",
                str(output),
                "--source-up",
                args.source_up,
                "--source-front",
                args.source_front,
                "--unit-scale",
                str(args.unit_scale),
            ],
            check=False,
        )
        return completed.returncode
    if args.command == "convert-infinigen":
        manifest = InfinigenIndoorsAdapter(_categories(args)).discover(
            args.raw_root, args.output_root, args.split
        )
        manifest.write(args.output_root / "manifests" / f"{args.split}.json")
        return 0
    if args.command == "convert-deepfurniture":
        DeepFurnitureAdapter(_categories(args)).convert(
            args.annotations, args.image_root, args.split
        ).write(args.output)
        return 0
    if args.command == "build-real-validation":
        RealValidationAdapter().build(
            args.source, args.image_root, args.annotations, args.depth_root
        ).write(args.output)
        return 0
    if args.command == "validate":
        validator = DataIntegrityValidator()
        reports = []
        for manifest in args.manifest:
            reports.append((str(manifest), validator.validate_manifest(manifest, not args.metadata_only)))
        if args.asset_metadata:
            reports.append(
                (
                    str(args.asset_metadata),
                    validator.validate_assets(
                        args.asset_metadata, set(args.allow_license), not args.metadata_only
                    ),
                )
            )
        failed = False
        for name, report in reports:
            print(json.dumps({"target": name, **asdict(report), "passed": report.passed}, ensure_ascii=False))
            failed |= not report.passed
        return 1 if failed else 0
    return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
