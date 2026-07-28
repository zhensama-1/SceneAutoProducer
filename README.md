# Editable 2D-to-Blender Scene Pipeline

This project implements a three-stage pipeline for converting one or more 2D input images into a semantic, editable Blender scene:

1. **Scene Initialization**: detect objects, refine masks, reconstruct coarse meshes, and estimate rough transforms.
2. **Multi-Agent Blender Scene IR and Code Generation Loop**: run a fixed Scene Planner -> Code Compiler -> Blender Execution/Validation -> Revision loop before emitting final IR and `bpy` code.
3. **Asset / Procedural Geometry Enrichment**: replace or supplement rough meshes with editable assets and procedural assemblies.

The implementation is intentionally modular. Grounded-SAM, SAM3D, or other model-backed components can be plugged in later through small adapter interfaces, while the local fallback path remains deterministic and testable.

## Quick Start

```powershell
python -m src.pipeline.cli --demo --scene-id demo_room --output-dir outputs\demo_room --step2-iterations 3
python -m unittest discover -s tests
```

For your own images, place them under `data/inputs/` and run:

```powershell
python -m src.pipeline.cli --inputs data\inputs\room_001.jpg --scene-id room_001 --output-dir outputs\room_001
```

The demo command writes:

- `outputs/demo_room/scene_initialization/demo_room.init.json`
- `outputs/demo_room/scene_ir/scene_iter_1.json`
- `outputs/demo_room/blender_scripts/scene_iter_1.py`
- `outputs/demo_room/reports/validation_iter_1.json`
- `outputs/demo_room/reports/revision_iter_1.json`
- `outputs/demo_room/scene_ir/final_scene_ir.json`
- `outputs/demo_room/blender_scripts/final_blender_script.py`
- `outputs/demo_room/reports/final_validation_report.json`
- `outputs/demo_room/reports/iteration_history.json`

If Blender is installed and available on `PATH`, run:

```powershell
python -m src.pipeline.cli --demo --scene-id demo_room --output-dir outputs\demo_room --run-blender
```

The generated Blender script is repeatable and saves the `.blend` file declared in Scene IR.
The standalone JSON Schema is available at `src/blender_ir/blender_scene_ir.schema.json`.

## Architecture

```text
src/
  pipeline/
    cli.py
    run_pipeline.py
    config.py
    step2_loop.py

  step1_scene_initialization/
    orchestrator.py
    schemas.py
    detection/
    mask_refinement/
    reconstruction/
    pose_estimation/

  step2_blender_generation/
    orchestrator.py
    schemas.py
    agents/
    scene_ir/
    codegen/
    execution/
    validation/
    loop/

  step3_asset_enrichment/
    orchestrator.py
    schemas.py
    strategy/
    asset_library/
    procedural_modeling/
    fitting/
    materials/
    assembly/

  common/
    llm/
    io/
    geometry/
    blender/
    validation/
    logging/

  prompts/
    step1/
    step2/
    step3/
```

The older compact modules (`scene_initialization`, `scene_planner`, `bpy_compiler`,
`asset_retrieval`, `procedural_modeling`, and `validation`) remain as stable
implementation modules. The `step*_...` packages provide the larger production
architecture and adapter boundaries for model-backed replacements.

## Design Principles

- Never collapse the entire image into one opaque 3D shell.
- Preserve semantic object identity in IR and Blender collections.
- Prefer procedural geometry for architecture and structured furniture.
- Prefer editable asset replacement for furniture, lights, and decorations.
- Keep reconstructed meshes only when no better editable representation is available.
- Generate Blender Python from a fixed compiler, not from unconstrained model output.

## Step 2 Multi-Agent Loop

Step 2 is implemented as a four-module closed loop. The default loop count is `k=3`, configurable with `--step2-iterations`.

```text
Step 1 Scene Initialization JSON
  |
  v
[Agent 1] Scene Planner Agent
  |
  v
[Agent 2] Blender Code Generator / Compiler Agent
  |
  v
[Agent 3] Blender Execution & Validation Agent
  |
  v
[Agent 4] Revision / Repair Agent
  |
  v
repeat until pass or k iterations are reached
```

Each iteration writes:

- `scene_ir/scene_iter_{i}.json`
- `blender_scripts/scene_iter_{i}.py`
- `scene_iter_{i}.blend` when `--run-blender` is enabled
- `renders/preview_iter_{i}.png` when Blender rendering succeeds
- `logs/blender_iter_{i}.log`
- `reports/validation_iter_{i}.json`
- `reports/revision_iter_{i}.json`

Final output uses the best/latest iteration:

- `scene_ir/final_scene_ir.json`
- `blender_scripts/final_blender_script.py`
- `final_scene.blend`
- `renders/final_preview.png`
- `reports/final_validation_report.json`
- `reports/iteration_history.json`

The compiler creates the required collection hierarchy (`Room`, `Furniture`, `Lighting`, `Camera`, `ReconstructedMeshes`, `ProceduralObjects`) and writes custom properties on generated Blender objects:

- `source_object_id`
- `category`
- `generation_strategy`
- `iteration`
