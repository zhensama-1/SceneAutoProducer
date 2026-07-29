from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class AssetMetadata:
    asset_id: str
    category: str
    style: str
    materials: list[str]
    dimensions: list[float]
    path: str
    license: str
    editable_parts: list[str]
    poly_count: int
    origin: str
    tags: list[str] = field(default_factory=list)
    source_id: str | None = None
    license_source: str | None = None
    commercial_use: bool | None = None
    front_axis: str | None = None
    up_axis: str = "Z"
    orientation_confidence: float = 0.0
    orientation_method: str = "unknown"
    normalized: bool = False
    quality_status: str = "unreviewed"
    content_hash: str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AssetMetadata":
        return cls(
            asset_id=str(data["asset_id"]),
            category=str(data["category"]),
            style=str(data.get("style", "generic")),
            materials=list(data.get("materials", [])),
            dimensions=[float(v) for v in data.get("dimensions", [1.0, 1.0, 1.0])],
            path=str(data.get("path", "")),
            license=str(data.get("license", "unknown")),
            editable_parts=list(data.get("editable_parts", [])),
            poly_count=int(data.get("poly_count", 0)),
            origin=str(data.get("origin", "local")),
            tags=list(data.get("tags", [])),
            source_id=data.get("source_id"),
            license_source=data.get("license_source"),
            commercial_use=data.get("commercial_use"),
            front_axis=data.get("front_axis"),
            up_axis=str(data.get("up_axis", "Z")),
            orientation_confidence=float(data.get("orientation_confidence", 0.0)),
            orientation_method=str(data.get("orientation_method", "unknown")),
            normalized=bool(data.get("normalized", False)),
            quality_status=str(data.get("quality_status", "unreviewed")),
            content_hash=data.get("content_hash"),
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class AssetLibrary:
    def __init__(self, assets: list[AssetMetadata]):
        self.assets = assets

    @classmethod
    def load(cls, metadata_path: Path | None) -> "AssetLibrary":
        if metadata_path is None or not metadata_path.exists():
            return cls([])
        data = json.loads(metadata_path.read_text(encoding="utf-8"))
        items = data.get("assets", data if isinstance(data, list) else [])
        return cls([AssetMetadata.from_dict(item) for item in items])

    def by_category(self, category: str) -> list[AssetMetadata]:
        return [asset for asset in self.assets if asset.category == category]
