from __future__ import annotations

import json
import sys
from pathlib import Path

SCRIPT_PATH = Path(__file__).resolve()
OUTPUT_ROOT = SCRIPT_PATH.parents[1]
REPO_ROOT = SCRIPT_PATH.parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.blender_ir.schema import BlenderSceneIR
from src.bpy_compiler.compiler import BlenderCodeCompiler


def load_portable_ir() -> BlenderSceneIR:
    ir_path = OUTPUT_ROOT / "scene_ir" / "demo_room.scene_ir.json"
    data = json.loads(ir_path.read_text(encoding="utf-8"))
    data["scene"]["output_blend"] = str(OUTPUT_ROOT / "demo_room.blend")
    data["scene"]["preview_render"] = str(OUTPUT_ROOT / "renders" / "demo_room.preview.png")
    for obj in data.get("objects", []):
        metadata = obj.get("metadata", {})
        source_mask = metadata.get("source_mask")
        if source_mask:
            metadata["source_mask"] = str(OUTPUT_ROOT / "masks" / Path(source_mask).name)
        source_path = obj.get("source_path")
        if source_path:
            obj["source_path"] = str(OUTPUT_ROOT / "recon" / Path(source_path).name)
    return BlenderSceneIR.from_dict(data)


def main() -> None:
    compiled_script = SCRIPT_PATH.with_name("demo_room.compiled_scene.py")
    BlenderCodeCompiler().compile(load_portable_ir(), compiled_script)
    exec(compile(compiled_script.read_text(encoding="utf-8"), str(compiled_script), "exec"), {"__name__": "__main__"})


if __name__ == "__main__":
    main()
