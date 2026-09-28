# /// script
# requires-python = ">=3.9"
# dependencies = ["pillow>=10"]
# ///
"""Copy images for blind decoding: strip all metadata and rename to image_NN.<ext>.

Usage: uv run prepare_images.py <image files or folders ...> --out <run folder>
Writes <out>/images/image_01.jpg ... and <out>/manifest.json (original name -> new name).
Decoders get only the images folder, never the manifest: file names, captions, EXIF,
GPS and XMP can leak what the photo is "about". Rotation from EXIF is applied first,
so the pixels look the same without the tag.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from PIL import Image, ImageOps

EXTS = {".jpg": ".jpg", ".jpeg": ".jpg", ".png": ".png", ".webp": ".png", ".gif": ".png",
        ".bmp": ".png", ".tif": ".png", ".tiff": ".png"}


def collect(paths) -> tuple:
    found, skipped = [], []
    for a in paths:
        p = Path(a)
        items = sorted(x for x in p.iterdir() if x.is_file()) if p.is_dir() else [p]
        for x in items:
            (found if x.suffix.lower() in EXTS else skipped).append(x)
    return found, skipped


def clean_copy(src: Path, dst: Path):
    with Image.open(src) as im:
        im = ImageOps.exif_transpose(im)
        if getattr(im, "n_frames", 1) > 1:
            im.seek(0)
        mode = "RGB" if dst.suffix == ".jpg" else ("RGBA" if "A" in im.getbands() else "RGB")
        clean = Image.new(mode, im.size)
        clean.paste(im.convert(mode))  # pixels only: no info dict, EXIF, ICC text or XMP carried over
        if dst.suffix == ".jpg":
            clean.save(dst, quality=95)
        else:
            clean.save(dst)


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("inputs", nargs="+"); ap.add_argument("--out", required=True)
    a = ap.parse_args(argv[1:])
    found, skipped = collect(a.inputs)
    for s in skipped:
        print(f"skipped (unsupported type; convert to JPEG or PNG first): {s.name}")
    if not found:
        print("No images found.")
        return 1
    out = Path(a.out); (out / "images").mkdir(parents=True, exist_ok=True)
    width = max(2, len(str(len(found))))
    manifest = {}
    for i, src in enumerate(found, 1):
        dst = out / "images" / f"image_{i:0{width}d}{EXTS[src.suffix.lower()]}"
        clean_copy(src, dst)
        manifest[str(src)] = dst.name
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"{len(found)} images cleaned into {out / 'images'}; manifest.json maps them back (keep it from decoders).")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
