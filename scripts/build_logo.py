#!/usr/bin/env python3
"""Build the circular paw logo used on the site (white disc + terracotta paw)."""

from __future__ import annotations

from pathlib import Path

try:
    from PIL import Image, ImageDraw
except ImportError:
    raise SystemExit("Install pillow in scripts/venv: ./venv/bin/pip install pillow")

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "assets" / "logo-icon.png"

# Site palette
ACCENT = (196, 120, 92)
WHITE = (255, 255, 255)


def draw_paw(draw: ImageDraw.ImageDraw, cx: float, cy: float, scale: float, color: tuple[int, int, int]) -> None:
    s = scale
    toes = [
        (cx - 14 * s, cy - 16 * s, 7 * s, 10 * s),
        (cx, cy - 20 * s, 7 * s, 10 * s),
        (cx + 14 * s, cy - 16 * s, 6.5 * s, 9 * s),
        (cx - 22 * s, cy - 4 * s, 6.5 * s, 9 * s),
    ]
    for x, y, w, h in toes:
        draw.ellipse([x - w, y - h, x + w, y + h], fill=color)
    draw.ellipse([cx - 18 * s, cy + 2 * s, cx + 18 * s, cy + 26 * s], fill=color)


def main() -> None:
    size = 176  # 2x for crisp PDF embed
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    pad = 6
    draw.ellipse([pad, pad, size - pad, size - pad], fill=WHITE)
    draw_paw(draw, size / 2, size / 2 + 4, 2.2, ACCENT)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    img.save(OUT, "PNG")
    print(f"Logo saved: {OUT}")


if __name__ == "__main__":
    main()
