from __future__ import annotations

from pathlib import Path

from src.asset_retrieval import AssetRetriever, AssetStrategyPlanner
from src.asset_retrieval.metadata import AssetLibrary
from src.blender_ir.schema import (
    BlenderSceneIR,
    CameraIR,
    ConstraintIR,
    LightIR,
    MaterialIR,
    ObjectIR,
    RelationIR,
    Transform,
)
from src.procedural_modeling import fit_dimensions_to_bbox, infer_material_for_category, procedural_spec_for_category


class ScenePlannerAgent:
    def __init__(self, asset_library: AssetLibrary | None = None, scene_style: str = "neutral"):
        self.asset_library = asset_library or AssetLibrary([])
        self.retriever = AssetRetriever(self.asset_library)
        self.strategy = AssetStrategyPlanner()
        self.scene_style = scene_style

    def plan(self, initialization: dict, output_root: Path, exports: list[str] | None = None) -> BlenderSceneIR:
        scene_id = initialization["scene_id"]
        output_root.mkdir(parents=True, exist_ok=True)
        material_map: dict[str, MaterialIR] = {}
        objects: list[ObjectIR] = []
        relations: list[RelationIR] = []
        constraints: list[ConstraintIR] = []

        floor_material = infer_material_for_category("floor", self.scene_style)
        wall_material = infer_material_for_category("wall", self.scene_style)
        material_map[floor_material.id] = floor_material
        material_map[wall_material.id] = wall_material

        objects.extend(self._architecture_objects(floor_material.id, wall_material.id))

        for init_obj in initialization.get("objects", []):
            category = str(init_obj.get("category", "object")).lower()
            dimensions = fit_dimensions_to_bbox(category, list(init_obj.get("scale", [1.0, 1.0, 1.0])), init_obj["bbox_2d"])
            position = self._ground_position(category, list(init_obj.get("position", [0.0, 0.0, dimensions[2] / 2])), dimensions)
            material = infer_material_for_category(category, self.scene_style)
            material_map.setdefault(material.id, material)
            asset = self.retriever.find_best(category, dimensions, self.scene_style)
            strategy = self.strategy.choose(category, asset is not None, float(init_obj.get("confidence", 0.5)))
            object_type = self._object_type_for_strategy(strategy, asset is not None)
            collection = self._collection_for(category, object_type)
            procedural = None
            asset_payload = None
            source_path = None
            editable_parts: list[str] = []
            if object_type == "procedural":
                procedural = procedural_spec_for_category(category, dimensions)
                editable_parts = self._editable_parts_for_procedural(category, init_obj["id"])
            elif object_type == "asset" and asset is not None:
                asset_payload = asset.to_dict()
                editable_parts = asset.editable_parts
            else:
                source_path = init_obj.get("mesh_path")

            objects.append(
                ObjectIR(
                    id=init_obj["id"],
                    name=init_obj["id"],
                    category=category,
                    collection=collection,
                    object_type=object_type,
                    transform=Transform(
                        position=position,
                        rotation_euler=list(init_obj.get("rotation_euler", [0.0, 0.0, 0.0])),
                        scale=[1.0, 1.0, 1.0],
                    ),
                    dimensions=dimensions,
                    material_id=material.id,
                    source_path=source_path,
                    primitive={"type": "cube"} if object_type == "primitive" else None,
                    asset=asset_payload,
                    procedural=procedural,
                    editable_parts=editable_parts,
                    metadata={
                        "source_mask": init_obj.get("mask_path"),
                        "source_bbox_2d": init_obj.get("bbox_2d"),
                        "source_confidence": init_obj.get("confidence"),
                        "asset_strategy": strategy,
                    },
                )
            )
            relations.append(RelationIR(subject=init_obj["id"], relation="on", target="floor_01", confidence=0.88))
            constraints.append(
                ConstraintIR(
                    object_id=init_obj["id"],
                    kind="grounded",
                    target="floor_01",
                    parameters={"min_z": 0.0, "snap_bottom_to_floor": True},
                )
            )

        scene = {
            "id": scene_id,
            "unit": initialization.get("unit", "meters"),
            "output_blend": str(output_root / f"{scene_id}.blend"),
            "preview_render": str(output_root / "renders" / f"{scene_id}.preview.png"),
            "exports": exports or [],
            "collections": sorted({obj.collection for obj in objects}),
        }

        lights = [
            LightIR(name="key_area_light", light_type="AREA", position=[-2.2, -3.2, 4.2], energy=520.0, size=4.0),
            LightIR(name="soft_fill_light", light_type="POINT", position=[2.8, 1.6, 2.8], energy=80.0, size=1.0),
        ]
        camera = CameraIR(position=[3.3, -4.4, 2.1], rotation_euler=[1.15, 0.0, 0.63], focal_length=32.0)
        return BlenderSceneIR(
            scene=scene,
            objects=objects,
            materials=list(material_map.values()),
            relations=relations,
            camera=camera,
            lights=lights,
            constraints=constraints,
        )

    def _architecture_objects(self, floor_mat: str, wall_mat: str) -> list[ObjectIR]:
        return [
            ObjectIR(
                id="floor_01",
                name="floor_01",
                category="floor",
                collection="Architecture",
                object_type="procedural",
                transform=Transform(position=[0.0, 0.0, -0.02]),
                dimensions=[4.4, 3.4, 0.04],
                material_id=floor_mat,
                procedural=procedural_spec_for_category("floor", [4.4, 3.4, 0.04]),
                editable_parts=["floor_slab"],
            ),
            ObjectIR(
                id="back_wall_01",
                name="back_wall_01",
                category="wall",
                collection="Architecture",
                object_type="procedural",
                transform=Transform(position=[0.0, 1.72, 1.35]),
                dimensions=[4.4, 0.08, 2.7],
                material_id=wall_mat,
                procedural=procedural_spec_for_category("wall", [4.4, 0.08, 2.7]),
                editable_parts=["wall_panel"],
            ),
        ]

    def _ground_position(self, category: str, position: list[float], dimensions: list[float]) -> list[float]:
        grounded = category not in {"wall", "window", "ceiling"}
        if grounded:
            position[2] = dimensions[2] / 2.0
        return [float(v) for v in position]

    def _object_type_for_strategy(self, strategy: str, has_asset: bool) -> str:
        if strategy == "procedural_modeling":
            return "procedural"
        if strategy == "replace_with_asset" and has_asset:
            return "asset"
        if strategy == "hybrid":
            return "procedural" if not has_asset else "asset"
        return "mesh"

    def _collection_for(self, category: str, object_type: str) -> str:
        if category in {"floor", "wall", "ceiling", "door", "window"}:
            return "Architecture"
        if object_type in {"asset", "procedural"}:
            return "Editable_Objects"
        return "Reconstructed_Meshes"

    def _editable_parts_for_procedural(self, category: str, object_id: str) -> list[str]:
        if category in {"table", "desk"}:
            return [
                f"{object_id}_top",
                f"{object_id}_leg_FL",
                f"{object_id}_leg_FR",
                f"{object_id}_leg_BL",
                f"{object_id}_leg_BR",
            ]
        if category in {"cabinet", "shelf", "bookcase"}:
            return [f"{object_id}_body"] + [f"{object_id}_shelf_{index:02d}" for index in range(1, 4)]
        return [f"{object_id}_body"]
