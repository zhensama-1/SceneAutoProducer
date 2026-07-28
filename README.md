# Editable 2D-to-Blender Scene Pipeline

This project implements a three-stage pipeline for converting one or more 2D input images into a semantic, editable Blender scene:

1. **Scene Initialization**: detect objects, refine masks, reconstruct coarse meshes, and estimate rough transforms.
2. **Blender Scene IR and Code Generation**: plan a structured Blender Scene IR, validate it, and compile deterministic `bpy` code.
3. **Asset / Procedural Geometry Enrichment**: replace or supplement rough meshes with editable assets and procedural assemblies.

The implementation is intentionally modular. Grounded-SAM, SAM3D, or other model-backed components can be plugged in later through small adapter interfaces, while the local fallback path remains deterministic and testable.

## Quick Start

```powershell
python -m src.pipeline.cli --demo --scene-id demo_room --output-dir outputs\demo_room
python -m unittest discover -s tests
```

The demo command writes:

- `outputs/demo_room/scene_initialization/demo_room.init.json`
- `outputs/demo_room/scene_ir/demo_room.scene_ir.json`
- `outputs/demo_room/blender_scripts/demo_room.build_scene.py`
- `outputs/demo_room/reports/demo_room.validation.json`
- `outputs/demo_room/reports/demo_room.validation.md`

If Blender is installed and available on `PATH`, run:

```powershell
python -m src.pipeline.cli --demo --scene-id demo_room --output-dir outputs\demo_room --run-blender
```

The generated Blender script is repeatable and saves the `.blend` file declared in Scene IR.
The standalone JSON Schema is available at `src/blender_ir/blender_scene_ir.schema.json`.

## Architecture

```text
inputs/
  image.png
    |
    v
src/scene_initialization/
src/mask_refinement/
src/mesh_reconstruction/
    |
    v
Scene Initialization JSON
    |
    v
src/scene_planner/
src/blender_ir/
src/bpy_compiler/
    |
    v
Blender Scene IR JSON + deterministic bpy script
    |
    v
src/asset_retrieval/
src/procedural_modeling/
src/validation/
```

## Design Principles

- Never collapse the entire image into one opaque 3D shell.
- Preserve semantic object identity in IR and Blender collections.
- Prefer procedural geometry for architecture and structured furniture.
- Prefer editable asset replacement for furniture, lights, and decorations.
- Keep reconstructed meshes only when no better editable representation is available.
- Generate Blender Python from a fixed compiler, not from unconstrained model output.
