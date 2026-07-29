from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from src.asset_retrieval.metadata import AssetMetadata
from src.data_integration.categories import CategoryRegistry


@dataclass
class AssetPolicy:
    license_allowlist: set[str]
    reject_unknown_license: bool = True
    require_normalized_orientation: bool = True
    max_poly_count: int = 500_000


@dataclass
class AssetCheck:
    accepted: bool
    reasons: list[str]


def inspect_glb(path: Path) -> list[str]:
    errors: list[str] = []
    if not path.exists():
        return ["model file does not exist"]
    if path.suffix.casefold() != ".glb":
        errors.append("model is not a GLB file")
        return errors
    with path.open("rb") as stream:
        if stream.read(4) != b"glTF":
            errors.append("invalid GLB header")
    return errors


def file_sha256(path: Path) -> str | None:
    if not path.exists() or not path.is_file():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


class AssetGate:
    def __init__(self, policy: AssetPolicy):
        self.policy = policy

    def check(self, asset: AssetMetadata, check_files: bool = True) -> AssetCheck:
        reasons: list[str] = []
        if self.policy.reject_unknown_license and asset.license.casefold() == "unknown":
            reasons.append("unknown license")
        if self.policy.license_allowlist and asset.license not in self.policy.license_allowlist:
            reasons.append(f"license not allowed: {asset.license}")
        if asset.commercial_use is False:
            reasons.append("asset disallows commercial use")
        if asset.poly_count < 0 or asset.poly_count > self.policy.max_poly_count:
            reasons.append(f"poly count outside policy: {asset.poly_count}")
        if len(asset.dimensions) != 3 or any(value <= 0 for value in asset.dimensions):
            reasons.append("invalid dimensions")
        if self.policy.require_normalized_orientation:
            if not asset.normalized:
                reasons.append("asset is not normalized")
            if asset.up_axis != "Z" or not asset.front_axis:
                reasons.append("orientation is not normalized to Z-up with a known front")
        if check_files:
            reasons.extend(inspect_glb(Path(asset.path)))
        return AssetCheck(not reasons, reasons)


class AssetCatalogBuilder:
    def __init__(self, categories: CategoryRegistry, policy: AssetPolicy):
        self.categories = categories
        self.gate = AssetGate(policy)

    def convert_record(self, source: str, item: dict[str, Any]) -> AssetMetadata:
        source_id = str(item.get("source_id") or item.get("asset_id") or item.get("uid") or item.get("id"))
        asset_id = str(item.get("asset_id") or f"{source}:{source_id}")
        if ":" not in asset_id:
            asset_id = f"{source}:{asset_id}"
        model_path = str(item.get("path") or item.get("glb_path") or "")
        path = Path(model_path)
        return AssetMetadata(
            asset_id=asset_id,
            category=self.categories.normalize(str(item.get("category", ""))),
            style=str(item.get("style", "generic")),
            materials=list(item.get("materials", [])),
            dimensions=[float(value) for value in item.get("dimensions", [1.0, 1.0, 1.0])],
            path=model_path,
            license=str(item.get("license", "unknown")),
            editable_parts=list(item.get("editable_parts", [])),
            poly_count=int(item.get("poly_count", 0)),
            origin=source,
            tags=list(item.get("tags", [])),
            source_id=source_id,
            license_source=item.get("license_source"),
            commercial_use=item.get("commercial_use"),
            front_axis=item.get("front_axis"),
            up_axis=str(item.get("up_axis", "Z")),
            orientation_confidence=float(item.get("orientation_confidence", 0.0)),
            orientation_method=str(item.get("orientation_method", "metadata")),
            normalized=bool(item.get("normalized", False)),
            quality_status=str(item.get("quality_status", "unreviewed")),
            content_hash=item.get("content_hash") or file_sha256(path),
        )

    def build(
        self,
        source_files: list[tuple[str, Path]],
        check_files: bool = True,
        source_priority: tuple[str, ...] = ("abo", "objaverse_oa"),
    ) -> tuple[list[AssetMetadata], list[dict[str, Any]]]:
        accepted: list[AssetMetadata] = []
        rejected: list[dict[str, Any]] = []
        for source, path in source_files:
            data = json.loads(path.read_text(encoding="utf-8"))
            for item in data.get("assets", data if isinstance(data, list) else []):
                asset = self.convert_record(source, item)
                result = self.gate.check(asset, check_files=check_files)
                asset.quality_status = "accepted" if result.accepted else "quarantined"
                if result.accepted:
                    accepted.append(asset)
                else:
                    rejected.append({"asset": asset.to_dict(), "reasons": result.reasons})

        priority = {source: index for index, source in enumerate(source_priority)}
        accepted.sort(key=lambda item: priority.get(item.origin, len(priority)))
        deduplicated: list[AssetMetadata] = []
        seen: set[tuple[Any, ...]] = set()
        for asset in accepted:
            signature: tuple[Any, ...]
            if asset.content_hash:
                signature = ("hash", asset.content_hash)
            else:
                signature = (
                    "shape",
                    asset.category,
                    *(round(value, 3) for value in asset.dimensions),
                )
            if signature in seen:
                rejected.append({"asset": asset.to_dict(), "reasons": ["cross-library duplicate"]})
                continue
            seen.add(signature)
            deduplicated.append(asset)
        return deduplicated, rejected
