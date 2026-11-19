"""Page images prepared for a vision model (`mmo ocr images`): upright by EXIF, grayscale, long side limited.

The pixels are not rotated beyond the EXIF orientation: the model reads a photo taken sideways as it is and reports
the rotation (`ROTATION:` line, stored by `mmo ocr import`).
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageOps

from mmo.core.topic import Source


def prepare_images(
    source: Source, out_dir: Path, scans: set[int] | None = None, skip: set[int] | None = None, size: int = 1600
) -> list[int]:
    """Write `scan-NNNN.jpg` for each chosen scan into `out_dir`; return the scans written."""
    out_dir.mkdir(parents=True, exist_ok=True)
    written = []
    for page in source.pages():
        if (scans is not None and page.scan not in scans) or (skip and page.scan in skip):
            continue
        with Image.open(page.image) as image:
            upright = ImageOps.exif_transpose(image).convert("L")
        upright.thumbnail((size, size))
        upright.save(out_dir / f"scan-{page.scan:04d}.jpg", quality=85)
        written.append(page.scan)
    return written
