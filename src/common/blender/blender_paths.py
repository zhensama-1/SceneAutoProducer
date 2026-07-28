from __future__ import annotations

import shutil


def blender_executable(name: str = "blender") -> str:
    return shutil.which(name) or name
