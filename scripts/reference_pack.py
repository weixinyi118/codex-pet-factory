#!/usr/bin/env python3
"""Create a bounded JPEG reference pack without exposing images to chat history."""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import math
import re
from pathlib import Path

from PIL import Image, ImageOps


def slug(value: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9._-]+", "-", value).strip("-.")
    return cleaned or "reference"


def flatten_to_rgb(image: Image.Image) -> Image.Image:
    image = ImageOps.exif_transpose(image)
    if image.mode in {"RGBA", "LA"} or "transparency" in image.info:
        rgba = image.convert("RGBA")
        background = Image.new("RGBA", rgba.size, (255, 255, 255, 255))
        return Image.alpha_composite(background, rgba).convert("RGB")
    return image.convert("RGB")


def encode_jpeg(image: Image.Image, quality: int) -> bytes:
    buffer = io.BytesIO()
    image.save(buffer, format="JPEG", quality=quality, optimize=True, progressive=True, subsampling="4:2:0")
    return buffer.getvalue()


def fit_image(source: Path, max_edge: int, target_bytes: int) -> tuple[bytes, tuple[int, int], int]:
    with Image.open(source) as opened:
        image = flatten_to_rgb(opened)

    if max(image.size) > max_edge:
        scale = max_edge / max(image.size)
        image = image.resize((max(1, round(image.width * scale)), max(1, round(image.height * scale))), Image.Resampling.LANCZOS)

    for _ in range(12):
        best: tuple[bytes, int] | None = None
        low, high = 42, 92
        while low <= high:
            quality = (low + high) // 2
            payload = encode_jpeg(image, quality)
            if len(payload) <= target_bytes:
                best = (payload, quality)
                low = quality + 1
            else:
                high = quality - 1
        if best:
            return best[0], image.size, best[1]
        next_width = max(1, math.floor(image.width * 0.84))
        next_height = max(1, math.floor(image.height * 0.84))
        if (next_width, next_height) == image.size:
            break
        image = image.resize((next_width, next_height), Image.Resampling.LANCZOS)

    payload = encode_jpeg(image, 40)
    if len(payload) > target_bytes:
        raise ValueError(f"Could not fit {source} below {target_bytes} bytes")
    return payload, image.size, 40


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("images", nargs="+", type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--max-total-mib", type=float, default=5.0)
    parser.add_argument("--max-file-mib", type=float, default=1.5)
    parser.add_argument("--max-edge", type=int, default=1600)
    args = parser.parse_args()

    sources = [path.expanduser().resolve() for path in args.images]
    missing = [str(path) for path in sources if not path.is_file()]
    if missing:
        raise SystemExit("Missing reference image(s): " + ", ".join(missing))

    output_dir = args.output_dir.expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    max_total = max(1, round(args.max_total_mib * 1024 * 1024))
    max_file = max(1, round(args.max_file_mib * 1024 * 1024))
    per_image = min(max_file, max_total // len(sources))

    records = []
    total = 0
    for index, source in enumerate(sources, start=1):
        payload, size, quality = fit_image(source, args.max_edge, per_image)
        destination = output_dir / f"{index:02d}-{slug(source.stem)}.jpg"
        destination.write_bytes(payload)
        total += len(payload)
        records.append(
            {
                "source": str(source),
                "packed": str(destination),
                "bytes": len(payload),
                "width": size[0],
                "height": size[1],
                "jpeg_quality": quality,
                "sha256": hashlib.sha256(payload).hexdigest(),
            }
        )

    if total > max_total:
        raise SystemExit(f"Packed references exceed cap: {total} > {max_total}")

    manifest = {
        "version": 1,
        "max_total_bytes": max_total,
        "max_file_bytes": per_image,
        "total_bytes": total,
        "count": len(records),
        "references": records,
    }
    manifest_path = output_dir / "reference-manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"ok": True, "manifest": str(manifest_path), "total_bytes": total, "count": len(records)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
