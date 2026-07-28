from __future__ import annotations

from pathlib import Path
from typing import Any

from src.common.io.json_io import write_json


class ReportWriter:
    def write_json(self, path: Path, data: Any) -> Path:
        return write_json(path, data)
