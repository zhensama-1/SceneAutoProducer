# SceneAutoProducer

This repository contains a complete reproducible snapshot of the SceneAutoProducer project under `snapshots/`.

The local project was prepared as a normal Git repository with commit `182f673` (`Initial SceneAutoProducer pipeline`). Direct `git push` from the current Windows shell was blocked by HTTPS connection resets and missing SSH key access, so the full project tree was uploaded as a split base64 ZIP snapshot.

## Restore the project

From the repository root after cloning:

```powershell
$b64 = (Get-ChildItem snapshots\SceneAutoProducer.snapshot.zip.b64.part* | Sort-Object Name | ForEach-Object { Get-Content -Raw $_.FullName }) -join ''
[IO.File]::WriteAllBytes('SceneAutoProducer.snapshot.zip', [Convert]::FromBase64String($b64))
Expand-Archive SceneAutoProducer.snapshot.zip -DestinationPath . -Force
```

Then validate:

```powershell
python -m compileall src tests
python -m unittest discover -s tests
python -m src.pipeline.cli --demo --scene-id demo_room --output-dir outputs\demo_room
```

If Blender is installed and available on `PATH`:

```powershell
python -m src.pipeline.cli --demo --scene-id demo_room --output-dir outputs\demo_room --run-blender
```

## What is inside

- Three-stage 2D image to editable Blender scene pipeline
- Scene initialization adapters and local fallback
- Stable Blender Scene IR plus JSON Schema
- Deterministic `bpy` compiler
- Asset retrieval strategy and procedural modeling specs
- Validation reports and demo outputs
