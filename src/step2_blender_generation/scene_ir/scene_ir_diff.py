from __future__ import annotations

from typing import Any


def diff_scene_ir(before: dict[str, Any], after: dict[str, Any]) -> dict[str, Any]:
    return {
        "scene_changed": before.get("scene") != after.get("scene"),
        "object_count_before": len(before.get("objects", [])),
        "object_count_after": len(after.get("objects", [])),
        "material_count_before": len(before.get("materials", [])),
        "material_count_after": len(after.get("materials", [])),
    }
