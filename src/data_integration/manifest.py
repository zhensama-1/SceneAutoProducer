from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class ManifestRecord:
    sample_id: str
    source: str
    split: str
    modalities: dict[str, str]
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ManifestRecord":
        return cls(
            sample_id=str(data["sample_id"]),
            source=str(data["source"]),
            split=str(data.get("split", "unspecified")),
            modalities={str(k): str(v) for k, v in data.get("modalities", {}).items()},
            metadata=dict(data.get("metadata", {})),
        )


@dataclass
class DataManifest:
    source: str
    records: list[ManifestRecord]
    version: int = 1
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def load(cls, path: Path) -> "DataManifest":
        data = json.loads(path.read_text(encoding="utf-8"))
        return cls(
            source=str(data["source"]),
            records=[ManifestRecord.from_dict(item) for item in data.get("records", [])],
            version=int(data.get("version", 1)),
            metadata=dict(data.get("metadata", {})),
        )

    def write(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(
                {
                    "version": self.version,
                    "source": self.source,
                    "metadata": self.metadata,
                    "records": [asdict(item) for item in self.records],
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
