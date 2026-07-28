from __future__ import annotations


class BlenderLogParser:
    def errors(self, log_text: str) -> list[str]:
        return [line for line in log_text.splitlines() if "ERROR" in line or "Traceback" in line]
