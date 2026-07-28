from __future__ import annotations

from pathlib import Path


class RenderValidator:
    def preview_exists(self, preview_path: Path) -> bool:
        return preview_path.exists() and preview_path.stat().st_size > 0
