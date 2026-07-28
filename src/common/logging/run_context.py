from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass
class RunContext:
    scene_id: str
    output_root: Path
