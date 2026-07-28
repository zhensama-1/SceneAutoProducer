from __future__ import annotations

import json


class ResponseParser:
    def parse_json(self, text: str) -> dict:
        return json.loads(text)
