"""Run inside Blender to normalize a GLB to meters, Z-up, -Y-front and floor origin."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import bpy
from mathutils import Matrix, Vector


AXES = {
    "X": Vector((1, 0, 0)),
    "-X": Vector((-1, 0, 0)),
    "Y": Vector((0, 1, 0)),
    "-Y": Vector((0, -1, 0)),
    "Z": Vector((0, 0, 1)),
    "-Z": Vector((0, 0, -1)),
}


def _args() -> argparse.Namespace:
    values = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--source-up", default="Z", choices=AXES)
    parser.add_argument("--source-front", default="-Y", choices=AXES)
    parser.add_argument("--unit-scale", type=float, default=1.0)
    return parser.parse_args(values)


def _alignment(source_up: str, source_front: str) -> Matrix:
    up = AXES[source_up]
    front = AXES[source_front]
    if abs(up.dot(front)) > 1e-6:
        raise ValueError("source up and front axes must be perpendicular")
    first = up.rotation_difference(AXES["Z"]).to_matrix().to_4x4()
    rotated_front = first @ front
    angle = rotated_front.xy.angle_signed(AXES["-Y"].xy)
    return Matrix.Rotation(angle, 4, "Z") @ first


def main() -> None:
    args = _args()
    source = Path(args.input).resolve()
    output = Path(args.output).resolve()
    if source == output:
        raise ValueError("output must differ from the original GLB")
    output.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    bpy.ops.import_scene.gltf(filepath=str(source))
    imported = list(bpy.context.scene.objects)
    roots = [obj for obj in imported if obj.parent is None]
    alignment = _alignment(args.source_up, args.source_front)
    scale = Matrix.Scale(args.unit_scale, 4)
    for root in roots:
        root.matrix_world = alignment @ scale @ root.matrix_world
    bpy.context.view_layer.update()
    mesh_objects = [obj for obj in imported if obj.type == "MESH"]
    if not mesh_objects:
        raise ValueError("GLB contains no mesh objects")
    corners = [obj.matrix_world @ Vector(corner) for obj in mesh_objects for corner in obj.bound_box]
    minimum = Vector((min(v.x for v in corners), min(v.y for v in corners), min(v.z for v in corners)))
    maximum = Vector((max(v.x for v in corners), max(v.y for v in corners), max(v.z for v in corners)))
    offset = Vector((-(minimum.x + maximum.x) / 2, -(minimum.y + maximum.y) / 2, -minimum.z))
    translation = Matrix.Translation(offset)
    for root in roots:
        root.matrix_world = translation @ root.matrix_world
    bpy.context.scene.unit_settings.system = "METRIC"
    bpy.context.scene.unit_settings.scale_length = 1.0
    bpy.ops.export_scene.gltf(
        filepath=str(output),
        export_format="GLB",
        use_selection=False,
        export_apply=True,
    )


if __name__ == "__main__":
    main()
