#!/usr/bin/env python3
"""Make a publication teaser at images/teasers/<id>.png.

  python3 scripts/make_teaser.py FIGURE ID [--page N] [--crop X,Y,W,H] [--margin 0.03]

FIGURE is a PNG/JPG/WebP image or a PDF (page N, default 1; needs `pdftoppm` from poppler
or PyMuPDF). The figure is flattened onto white, trimmed of empty margins, given a small even
margin, and scaled down to at most 1200 px wide and 600 px tall. Crop coordinates are pixels
of the source image, or of the page rendered at 220 dpi for a PDF.

The page shows teasers in a 2:1 box, so figures between about 1.6:1 and 3:1 fill it best.
Requires Pillow: pip install pillow
"""
from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

try:
    from PIL import Image, ImageChops
except ImportError:
    sys.exit("Pillow is missing. Install it with: pip install pillow")

ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "images" / "teasers"
DPI = 220


def load(source: Path, page: int) -> Image.Image:
    if source.suffix.lower() != ".pdf":
        return Image.open(source)
    if shutil.which("pdftoppm"):
        with tempfile.TemporaryDirectory() as tmp:
            stem = Path(tmp) / "page"
            subprocess.run(["pdftoppm", "-png", "-r", str(DPI), "-f", str(page), "-l", str(page),
                            "-singlefile", str(source), str(stem)], check=True)
            return Image.open(f"{stem}.png").copy()
    try:
        import fitz  # PyMuPDF
    except ImportError:
        sys.exit("PDF input needs poppler (pdftoppm) or PyMuPDF (pip install pymupdf).")
    pix = fitz.open(source)[page - 1].get_pixmap(dpi=DPI)
    return Image.frombytes("RGB", (pix.width, pix.height), pix.samples)


def on_white(im: Image.Image) -> Image.Image:
    im = im.convert("RGBA")
    canvas = Image.new("RGBA", im.size, (255, 255, 255, 255))
    canvas.alpha_composite(im)
    return canvas.convert("RGB")


def trim(im: Image.Image, tolerance: int = 12) -> Image.Image:
    diff = ImageChops.difference(im, Image.new("RGB", im.size, (255, 255, 255))).convert("L")
    box = diff.point(lambda v: 255 if v > tolerance else 0).getbbox()
    return im.crop(box) if box else im


def main() -> int:
    ap = argparse.ArgumentParser(description="Turn a paper figure into images/teasers/<id>.png")
    ap.add_argument("figure", type=Path, help="image file or PDF")
    ap.add_argument("id", help="publication id, e.g. duelrec (same as <article id>)")
    ap.add_argument("--page", type=int, default=1, help="PDF page number, starting at 1")
    ap.add_argument("--crop", help="X,Y,W,H in source pixels, applied before trimming")
    ap.add_argument("--margin", type=float, default=0.03, help="white margin as a fraction of the longer side")
    args = ap.parse_args()

    if not re.fullmatch(r"[a-z0-9][a-z0-9-]*", args.id):
        sys.exit("ID must use lowercase letters, digits and hyphens, matching the <article> id.")
    if not args.figure.exists():
        sys.exit(f"{args.figure} not found.")

    im = on_white(load(args.figure, args.page))
    if args.crop:
        try:
            x, y, w, h = (int(v) for v in args.crop.split(","))
        except ValueError:
            sys.exit("--crop takes four integers: X,Y,W,H")
        im = im.crop((x, y, x + w, y + h))
    im = trim(im)

    pad = round(max(im.size) * args.margin)
    framed = Image.new("RGB", (im.width + 2 * pad, im.height + 2 * pad), "white")
    framed.paste(im, (pad, pad))
    im = framed

    scale = min(1200 / im.width, 600 / im.height)
    if scale < 1:
        im = im.resize((round(im.width * scale), round(im.height * scale)), Image.LANCZOS)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out = OUT_DIR / f"{args.id}.png"
    im.save(out, optimize=True)
    if out.stat().st_size > 300 * 1024:
        im.quantize(colors=256, method=Image.Quantize.MEDIANCUT).save(out, optimize=True)

    ratio = im.width / im.height
    print(f"wrote {out.relative_to(ROOT)}  {im.width}x{im.height}  {ratio:.2f}:1  {out.stat().st_size / 1024:.0f} KB")
    if not 1.4 <= ratio <= 3.2:
        print("note: teasers sit in a 2:1 box, so this figure will look small. "
              "Use --crop to keep the main panel.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
