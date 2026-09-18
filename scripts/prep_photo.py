#!/usr/bin/env python3
"""
prep_photo.py — Step 1 of the ASCII-portrait pipeline.

Takes a normal photo and prepares it for ASCII conversion:
  1. Remove the background (rembg) so only the subject remains.
  2. Boost local contrast on the subject (OpenCV CLAHE) so a flatly-lit
     face gets real highlights/shadows instead of converting to a dark blob.
  3. Composite the subject onto pure white so the background maps to the
     blank end of the ASCII density ramp (white -> space).

Output is a grayscale PNG, ready for scripts/make_ascii_svg.py.

Usage:
    python scripts/prep_photo.py source-photo.jpg [-o source-prepped.png]
"""
import argparse
import sys

import cv2
import numpy as np
from PIL import Image
from rembg import remove


def remove_background(img: Image.Image) -> Image.Image:
    """Return an RGBA image with the background made transparent."""
    return remove(img)


def apply_clahe(rgb: np.ndarray) -> np.ndarray:
    """Boost local contrast via CLAHE on the L channel of LAB space.

    Contrast-limited adaptive histogram equalization works on local
    neighborhoods instead of the whole image, so it recovers highlights
    and shadows on a face without blowing out the rest of the frame.
    """
    lab = cv2.cvtColor(rgb, cv2.COLOR_RGB2LAB)
    l_channel, a_channel, b_channel = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8))
    l_eq = clahe.apply(l_channel)
    lab_eq = cv2.merge((l_eq, a_channel, b_channel))
    return cv2.cvtColor(lab_eq, cv2.COLOR_LAB2RGB)


def composite_on_white(rgba: Image.Image) -> Image.Image:
    """Flatten an RGBA cutout onto a pure white background.

    Pure white matters: it's the blank end of the ASCII density ramp,
    so anything outside the subject prints as empty space, not noise.
    """
    white_bg = Image.new("RGB", rgba.size, (255, 255, 255))
    white_bg.paste(rgba, mask=rgba.split()[3])
    return white_bg


def prep_photo(input_path: str, output_path: str) -> None:
    img = Image.open(input_path).convert("RGB")

    print("Removing background...", file=sys.stderr)
    cutout = remove_background(img)  # RGBA, subject isolated

    print("Boosting local contrast (CLAHE)...", file=sys.stderr)
    rgb = np.array(cutout.convert("RGB"))
    rgb_eq = apply_clahe(rgb)
    r_eq, g_eq, b_eq = Image.fromarray(rgb_eq).split()
    alpha = cutout.split()[3]
    cutout_eq = Image.merge("RGBA", (r_eq, g_eq, b_eq, alpha))

    print("Compositing onto white background...", file=sys.stderr)
    flattened = composite_on_white(cutout_eq)
    grayscale = flattened.convert("L")

    grayscale.save(output_path)
    print(f"Wrote {output_path}", file=sys.stderr)


def main():
    parser = argparse.ArgumentParser(
        description="Prep a photo for ASCII conversion (bg removal + CLAHE + white composite)."
    )
    parser.add_argument("input", help="Path to the source photo (jpg/png).")
    parser.add_argument(
        "-o", "--output", default="source-prepped.png",
        help="Output path for the prepped grayscale PNG (default: source-prepped.png)."
    )
    args = parser.parse_args()
    prep_photo(args.input, args.output)


if __name__ == "__main__":
    main()