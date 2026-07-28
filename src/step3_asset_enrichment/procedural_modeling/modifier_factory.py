from __future__ import annotations


class ModifierFactory:
    def bevel(self, width: float = 0.01, segments: int = 2) -> dict:
        return {"type": "BEVEL", "width": width, "segments": segments, "apply": False}
