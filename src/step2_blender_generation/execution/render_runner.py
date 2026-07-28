from __future__ import annotations

from pathlib import Path

from .blender_runner import BlenderRunner


class RenderRunner(BlenderRunner):
    def render_script(self, blender_exe: str, script_path: Path):
        return self.run_script(blender_exe, script_path)
