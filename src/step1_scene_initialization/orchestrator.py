from __future__ import annotations

from src.scene_initialization.initializer import SceneInitializer


class Step1SceneInitializationOrchestrator(SceneInitializer):
    """Step 1 facade over detection, mask refinement, reconstruction, and pose initialization."""
