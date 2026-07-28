from __future__ import annotations


class SchemaValidator:
    def validate_required_keys(self, data: dict, required: list[str]) -> list[str]:
        return [key for key in required if key not in data]
