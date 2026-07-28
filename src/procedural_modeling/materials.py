from __future__ import annotations

from src.blender_ir.schema import MaterialIR


_CATEGORY_COLORS = {
    "floor": [0.55, 0.48, 0.38, 1.0],
    "wall": [0.78, 0.80, 0.77, 1.0],
    "table": [0.48, 0.30, 0.18, 1.0],
    "desk": [0.48, 0.30, 0.18, 1.0],
    "cabinet": [0.58, 0.54, 0.46, 1.0],
    "shelf": [0.50, 0.38, 0.26, 1.0],
    "chair": [0.18, 0.22, 0.28, 1.0],
    "lamp": [0.85, 0.82, 0.70, 1.0],
}


def infer_material_for_category(category: str, scene_style: str = "neutral") -> MaterialIR:
    color = _CATEGORY_COLORS.get(category, [0.65, 0.65, 0.62, 1.0])
    if scene_style == "warm" and category not in {"chair"}:
        color = [min(1.0, color[0] + 0.05), min(1.0, color[1] + 0.03), color[2], color[3]]
    return MaterialIR(
        id=f"mat_{category}",
        name=f"{category}_editable_material",
        base_color=color,
        roughness=0.62 if category in {"floor", "wall"} else 0.48,
        metallic=0.0,
    )
