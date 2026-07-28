from __future__ import annotations


class LLMClient:
    """Minimal boundary for future hosted or local LLM calls."""

    def complete_json(self, prompt: str) -> dict:
        raise NotImplementedError("Configure an LLM backend before calling complete_json.")
