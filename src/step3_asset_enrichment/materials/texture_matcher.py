from __future__ import annotations


class TextureMatcher:
    def match(self, category: str, candidates: list[str]) -> str | None:
        return candidates[0] if candidates else None
