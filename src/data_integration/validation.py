from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

from src.asset_retrieval.metadata import AssetLibrary
from src.blender_ir.schema import BlenderSceneIR
from src.data_integration.assets import AssetGate, AssetPolicy
from src.data_integration.manifest import DataManifest


@dataclass
class ValidationReport:
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return not self.errors


class DataIntegrityValidator:
    def validate_manifest(self, path: Path, check_files: bool = True) -> ValidationReport:
        report = ValidationReport()
        try:
            manifest = DataManifest.load(path)
        except (OSError, KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
            report.errors.append(f"cannot load manifest {path}: {exc}")
            return report
        ids: set[str] = set()
        for record in manifest.records:
            if record.sample_id in ids:
                report.errors.append(f"duplicate sample id: {record.sample_id}")
            ids.add(record.sample_id)
            if record.source != manifest.source:
                report.errors.append(f"{record.sample_id}: source differs from manifest")
            if not record.modalities:
                report.errors.append(f"{record.sample_id}: no modalities")
            if check_files:
                for modality, value in record.modalities.items():
                    candidate = Path(value)
                    if not candidate.is_absolute():
                        candidate = Path.cwd() / candidate
                    if not candidate.exists():
                        report.errors.append(f"{record.sample_id}: missing {modality}: {value}")
            scene_ir = record.modalities.get("scene_ir")
            if scene_ir:
                candidate = Path(scene_ir)
                if not candidate.is_absolute():
                    candidate = Path.cwd() / candidate
                if candidate.exists():
                    try:
                        BlenderSceneIR.from_dict(json.loads(candidate.read_text(encoding="utf-8")))
                    except (OSError, KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
                        report.errors.append(f"{record.sample_id}: invalid Scene IR: {exc}")
        if not manifest.records:
            report.warnings.append("manifest contains no records")
        return report

    def validate_assets(
        self,
        metadata_path: Path,
        allowlist: set[str],
        check_files: bool = True,
    ) -> ValidationReport:
        report = ValidationReport()
        library = AssetLibrary.load(metadata_path)
        gate = AssetGate(
            AssetPolicy(
                license_allowlist=allowlist,
                reject_unknown_license=True,
                require_normalized_orientation=True,
            )
        )
        ids: set[str] = set()
        for asset in library.assets:
            if asset.asset_id in ids:
                report.errors.append(f"duplicate asset id: {asset.asset_id}")
            ids.add(asset.asset_id)
            result = gate.check(asset, check_files=check_files)
            report.errors.extend(f"{asset.asset_id}: {reason}" for reason in result.reasons)
        if not library.assets:
            report.warnings.append("asset catalog contains no assets")
        return report
