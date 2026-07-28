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
