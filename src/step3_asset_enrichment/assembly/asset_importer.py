from __future__ import annotations

from pathlib import Path


class AssetImporter:
    def resolve_path(self, path: str) -> Path:
        resolved = Path(path).resolve()
        if resolved.suffix.casefold() != ".glb":
            raise ValueError(f"Only GLB assets are supported, got: {resolved}")
        if not resolved.exists():
            raise FileNotFoundError(resolved)
        return resolved

    def blender_import_statement(self, path: str) -> str:
        resolved = self.resolve_path(path)
        escaped = str(resolved).replace("\\", "\\\\").replace('"', '\\"')
        return f'bpy.ops.import_scene.gltf(filepath="{escaped}")'
