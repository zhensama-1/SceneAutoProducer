from __future__ import annotations

import json
from pathlib import Path


class CategoryRegistry:
    def __init__(self, aliases: dict[str, str], unknown: str = "unknown"):
        self.aliases = aliases
        self.unknown = unknown

    @classmethod
    def load(cls, path: Path) -> "CategoryRegistry":
        data = json.loads(path.read_text(encoding="utf-8"))
        aliases: dict[str, str] = {}
        for canonical, values in data.get("categories", {}).items():
            aliases[canonical.casefold()] = canonical
            for value in values:
                aliases[str(value).strip().casefold()] = canonical
        return cls(aliases, str(data.get("unknown", "unknown")))

    def normalize(self, label: str | None) -> str:
        if not label:
            return self.unknown
        return self.aliases.get(label.strip().casefold(), self.unknown)
