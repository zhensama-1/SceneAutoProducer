from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from src.data_integration.adapters import InfinigenIndoorsAdapter, RealValidationAdapter
from src.data_integration.assets import AssetCatalogBuilder, AssetPolicy
from src.data_integration.categories import CategoryRegistry
from src.data_integration.manifest import DataManifest, ManifestRecord
from src.data_integration.validation import DataIntegrityValidator


class DataIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.categories = CategoryRegistry.load(Path("configs/categories.json"))

    def test_categories_are_shared_across_sources(self):
        self.assertEqual(self.categories.normalize("Dining Chair"), "chair")
        self.assertEqual(self.categories.normalize("couch"), "sofa")
        self.assertEqual(self.categories.normalize("not-a-category"), "unknown")

    def test_asset_gate_rejects_license_and_deduplicates_across_sources(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            model = root / "chair.glb"
            model.write_bytes(b"glTF" + b"\x00" * 20)
            base = {
                "category": "dining chair",
                "path": str(model),
                "dimensions": [0.5, 0.5, 0.8],
                "poly_count": 100,
                "license": "CC-BY-4.0",
                "commercial_use": True,
                "front_axis": "-Y",
                "up_axis": "Z",
                "normalized": True,
            }
            abo = root / "abo.json"
            objaverse = root / "objaverse.json"
            abo.write_text(json.dumps({"assets": [{**base, "asset_id": "chair-1"}]}), encoding="utf-8")
            objaverse.write_text(
                json.dumps(
                    {
                        "assets": [
                            {**base, "asset_id": "duplicate-chair"},
                            {**base, "asset_id": "blocked", "license": "unknown"},
                        ]
                    }
                ),
                encoding="utf-8",
            )
            builder = AssetCatalogBuilder(
                self.categories,
                AssetPolicy({"CC-BY-4.0"}, require_normalized_orientation=True),
            )
            accepted, rejected = builder.build(
                [("abo", abo), ("objaverse_oa", objaverse)], check_files=True
            )
            self.assertEqual([item.asset_id for item in accepted], ["abo:chair-1"])
            reasons = [reason for item in rejected for reason in item["reasons"]]
            self.assertIn("cross-library duplicate", reasons)
            self.assertIn("unknown license", reasons)

    def test_infinigen_converts_scene_ir_and_manifest(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            scene = root / "raw" / "scene_001"
            scene.mkdir(parents=True)
            (scene / "rgb.png").write_bytes(b"rgb")
            (scene / "instance_mask.png").write_bytes(b"mask")
            (scene / "depth.png").write_bytes(b"depth")
            (scene / "cameras.json").write_text(
                json.dumps({"width": 640, "fx": 700, "position": [1, 2, 3]}),
                encoding="utf-8",
            )
            (scene / "layout.json").write_text(
                json.dumps({"objects": [{"id": "c1", "category": "armchair", "size": [1, 1, 1]}]}),
                encoding="utf-8",
            )
            output = root / "processed" / "infinigen_indoors"
            manifest = InfinigenIndoorsAdapter(self.categories).discover(root / "raw", output, "train")
            self.assertEqual(len(manifest.records), 1)
            ir = json.loads((output / "scene_ir" / "scene_001.scene_ir.json").read_text(encoding="utf-8"))
            self.assertEqual(ir["objects"][0]["category"], "chair")
            self.assertEqual(ir["scene"]["coordinate_system"], "Z-up")

    def test_real_validation_is_marked_non_training(self):
        with tempfile.TemporaryDirectory() as temp:
            images = Path(temp) / "images"
            images.mkdir()
            (images / "room.jpg").write_bytes(b"image")
            manifest = RealValidationAdapter().build("custom", images, None)
            self.assertFalse(manifest.metadata["training_allowed"])
            self.assertEqual(manifest.records[0].split, "real_val")

    def test_integrity_validator_detects_duplicate_samples(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "manifest.json"
            record = ManifestRecord("same", "test", "val", {"rgb": "missing.jpg"})
            DataManifest("test", [record, record]).write(path)
            report = DataIntegrityValidator().validate_manifest(path, check_files=False)
            self.assertFalse(report.passed)
            self.assertTrue(any("duplicate sample id" in item for item in report.errors))


if __name__ == "__main__":
    unittest.main()
