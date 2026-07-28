from __future__ import annotations

from pathlib import Path

from .types import DetectedObject


class BaseObjectDetector:
    """Adapter boundary for Grounded-SAM, Detic, OWL-ViT+SAM, or hosted vision models."""

    def detect(self, image_path: Path, output_mask_dir: Path) -> list[DetectedObject]:
        raise NotImplementedError


class HeuristicObjectDetector(BaseObjectDetector):
    """Local fallback detector.

    It uses simple foreground bounding boxes when Pillow is available. This is not a semantic model;
    it exists so the pipeline can be exercised without GPU checkpoints.
    """

    def detect(self, image_path: Path, output_mask_dir: Path) -> list[DetectedObject]:
        output_mask_dir.mkdir(parents=True, exist_ok=True)
        bbox = self._foreground_bbox(image_path)
        obj_id = f"{image_path.stem}_object_01"
        mask_path = output_mask_dir / f"{obj_id}.png"
        self._write_rect_mask(image_path, mask_path, bbox)
        return [
            DetectedObject(
                id=obj_id,
                category="object",
                bbox_2d=bbox,
                confidence=0.52,
                mask_path=str(mask_path),
                image_path=str(image_path),
            )
        ]

    def _foreground_bbox(self, image_path: Path) -> list[int]:
        try:
            from PIL import Image
        except ImportError:
            return [80, 80, 560, 420]

        with Image.open(image_path).convert("RGB") as image:
            width, height = image.size
            pixels = image.load()
            xs: list[int] = []
            ys: list[int] = []
            for y in range(0, height, max(1, height // 160)):
                for x in range(0, width, max(1, width // 160)):
                    r, g, b = pixels[x, y]
                    if min(abs(r - 255), abs(g - 255), abs(b - 255)) > 20 and (r + g + b) < 735:
                        xs.append(x)
                        ys.append(y)
            if not xs or not ys:
                margin_x = max(1, width // 5)
                margin_y = max(1, height // 5)
                return [margin_x, margin_y, width - margin_x, height - margin_y]
            pad_x = max(4, width // 80)
            pad_y = max(4, height // 80)
            return [
                max(0, min(xs) - pad_x),
                max(0, min(ys) - pad_y),
                min(width, max(xs) + pad_x),
                min(height, max(ys) + pad_y),
            ]

    def _write_rect_mask(self, image_path: Path, mask_path: Path, bbox: list[int]) -> None:
        try:
            from PIL import Image, ImageDraw
        except ImportError:
            mask_path.write_bytes(b"")
            return

        with Image.open(image_path) as image:
            mask = Image.new("L", image.size, 0)
            draw = ImageDraw.Draw(mask)
            draw.rectangle(bbox, fill=255)
            mask.save(mask_path)
