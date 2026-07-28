from __future__ import annotations

from pathlib import Path


class CodeRepairAgent:
    """Minimal deterministic repair pass for known Blender API drift."""

    REPLACEMENTS = {
        "inputs['Base Color']": "inputs.get('Base Color')",
        "inputs['Roughness']": "inputs.get('Roughness')",
        "inputs['Metallic']": "inputs.get('Metallic')",
    }

    def repair(self, script_path: Path, blender_error: str) -> bool:
        text = script_path.read_text(encoding="utf-8")
        repaired = text
        if "KeyError" in blender_error and "inputs" in blender_error:
            for old, new in self.REPLACEMENTS.items():
                repaired = repaired.replace(old, new)
        if repaired != text:
            script_path.write_text(repaired, encoding="utf-8")
            return True
        return False
