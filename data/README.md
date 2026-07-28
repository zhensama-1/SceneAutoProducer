# Data Directory

Place your own input images here when running SceneAutoProducer.

Suggested layout:

```text
data/
  inputs/
    room_001.jpg
    room_002.png
  masks/
  recon/
```

Example:

```bash
python -m src.pipeline.cli \
  --inputs data/inputs/room_001.jpg \
  --scene-id room_001 \
  --output-dir outputs/room_001
```

With Blender enabled:

```bash
python -m src.pipeline.cli \
  --inputs data/inputs/room_001.jpg \
  --scene-id room_001 \
  --output-dir outputs/room_001 \
  --run-blender \
  --blender-exe "$BLENDER_EXE"
```
