"""Rectify reference photos of a display to a flat, glass-only image.

Reads a manifest (JSON) next to the output folder:
    {"size": [w, h], "images": {"out.png": {"source": "../frame.png",
      "corners": [[x, y] top-left, top-right, bottom-right, bottom-left]}}}
Corner pixels are measured by eye on the source frame. Layout Studio fits the
results to the measured glass, so the stored aspect does not need to match it.

    python tools/cockpit/rectify_reference.py "docs/reference/CockpitImages/DEP(DATA_ENTRY_PANEL)/rectified/corners.json"
"""
import argparse
import json
from pathlib import Path

from PIL import Image


def perspective_coefficients(target, source):
    """Coefficients mapping output pixels (target quad) to input pixels (source quad)."""
    rows, values = [], []
    for (x, y), (u, v) in zip(target, source):
        rows.append([x, y, 1, 0, 0, 0, -u*x, -u*y]); values.append(u)
        rows.append([0, 0, 0, x, y, 1, -v*x, -v*y]); values.append(v)
    # Solve the 8x8 system with Gaussian elimination (no numpy dependency).
    n = len(rows)
    m = [row+[value] for row, value in zip(rows, values)]
    for col in range(n):
        pivot = max(range(col, n), key=lambda r: abs(m[r][col]))
        m[col], m[pivot] = m[pivot], m[col]
        for r in range(n):
            if r != col:
                f = m[r][col]/m[col][col]
                m[r] = [a-f*b for a, b in zip(m[r], m[col])]
    return [m[i][n]/m[i][i] for i in range(n)]


def rectify(source, corners, size):
    w, h = size
    target = [(0, 0), (w, 0), (w, h), (0, h)]
    image = Image.open(source).convert('RGB')
    return image.transform((w, h), Image.Transform.PERSPECTIVE,
                           perspective_coefficients(target, corners), Image.Resampling.BICUBIC)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('manifest', type=Path)
    args = parser.parse_args()
    manifest = json.loads(args.manifest.read_text(encoding='utf-8'))
    folder = args.manifest.parent
    for name, entry in manifest['images'].items():
        out = folder/name
        rectify(folder/entry['source'], entry['corners'], manifest['size']).save(out)
        print(out)


if __name__ == '__main__':
    main()
