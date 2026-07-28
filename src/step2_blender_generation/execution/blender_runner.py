from __future__ import annotations

import shutil
import subprocess
from pathlib import Path


class BlenderRunner:
    def run_script(self, blender_exe: str, script_path: Path) -> subprocess.CompletedProcess[str]:
        executable = shutil.which(blender_exe) or blender_exe
        return subprocess.run([executable, "--background", "--python", str(script_path)], capture_output=True, text=True, check=False)
