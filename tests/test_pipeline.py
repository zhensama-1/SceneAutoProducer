from __future__ import annotations

import json
import tempfile
import unittest
from argparse import Namespace
from pathlib import Path

from src.pipeline.cli import run_pipeline


class PipelineTests(unittest.TestCase):
    def test_demo_pipeline_generates_ir_and_script(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            outputs = run_pipeline(
                Namespace(
                    inputs=[],
                    demo=True,
                    scene_id="unit_demo",
                    output_dir=temp_dir,
                    asset_metadata="assets/metadata/assets.json",
                    scene_style="neutral",
                    export=[],
                    step2_iterations=3,
                    run_blender=False,
                    blender_exe="blender",
                )
            )
            self.assertTrue(outputs["initialization"].exists())
            self.assertTrue(outputs["scene_ir"].exists())
            self.assertTrue(outputs["script"].exists())
            self.assertTrue(outputs["report"].exists())
            self.assertTrue(outputs["history"].exists())
            ir = json.loads(outputs["scene_ir"].read_text(encoding="utf-8"))
            object_ids = {item["id"] for item in ir["objects"]}
            self.assertIn("floor_01", object_ids)
            self.assertIn("table_01", object_ids)
            self.assertEqual(ir["scene"]["coordinate_system"], "Z-up")
            self.assertIn("Room", ir["scene"]["collections"])
            table = next(item for item in ir["objects"] if item["id"] == "table_01")
            self.assertEqual(table["object_type"], "procedural")
            script = outputs["script"].read_text(encoding="utf-8")
            self.assertIn("def create_table", script)
            self.assertIn("source_object_id", script)
            self.assertIn("save_as_mainfile", script)
            history = json.loads(outputs["history"].read_text(encoding="utf-8"))
            self.assertGreaterEqual(len(history), 1)


if __name__ == "__main__":
    unittest.main()
