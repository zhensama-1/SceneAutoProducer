from __future__ import annotations


def should_stop(validation_report: dict) -> bool:
    return validation_report.get("status") == "pass"
