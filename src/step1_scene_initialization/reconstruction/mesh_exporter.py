from __future__ import annotations

from pathlib import Path


class MeshExporter:
    def export_obj(self, source_path: Path, target_path: Path) -> Path:
        target_path.parent.mkdir(parents=True, exist_ok=True)
        target_path.write_text(source_path.read_text(encoding="utf-8"), encoding="utf-8")
        return target_path
