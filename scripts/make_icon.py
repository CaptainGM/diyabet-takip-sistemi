"""Uygulama ikonunu üretir: assets/app.ico + assets/app.png.

Tasarım: mor→pembe gradient yuvarlatılmış kare zemin üzerinde beyaz damla
ve damlanın içinde kırmızı nabız (ECG) çizgisi.

Kullanım::

    python scripts/make_icon.py
"""

from __future__ import annotations

import pathlib

from PIL import Image, ImageDraw

ROOT = pathlib.Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"
S = 1024  # süper örnekleme boyutu
FINAL = 256


def _gradient(size: int) -> Image.Image:
    img = Image.new("RGB", (size, size))
    pixels = img.load()
    start = (124, 77, 255)   # #7c4dff
    end = (233, 30, 140)     # #e91e8c
    assert pixels is not None
    for y in range(size):
        for x in range(size):
            t = (x + y) / (2 * (size - 1))
            pixels[x, y] = (
                round(start[0] + (end[0] - start[0]) * t),
                round(start[1] + (end[1] - start[1]) * t),
                round(start[2] + (end[2] - start[2]) * t),
            )
    return img


def main() -> None:
    ASSETS.mkdir(exist_ok=True)

    # yuvarlatılmış kare maske
    mask = Image.new("L", (S, S), 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, S - 1, S - 1), radius=224, fill=255)

    canvas = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    canvas.paste(_gradient(S), (0, 0), mask)

    # beyaz damla: tepe üçgen + gövde elipsi
    droplet_mask = Image.new("L", (S, S), 0)
    d = ImageDraw.Draw(droplet_mask)
    cx, cy, r = 512, 590, 250
    d.polygon(
        [
            (cx, 176),
            (cx - 196, cy - 36),
            (cx + 196, cy - 36),
        ],
        fill=255,
    )
    d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=255)
    # damla hafif saydam beyaz
    canvas.paste(Image.new("RGBA", (S, S), (255, 255, 255, 240)), (0, 0), droplet_mask)

    # damla içinde nabız çizgisi (gradient pembe-kırmızı)
    pulse = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    p = ImageDraw.Draw(pulse)
    points = [
        (322, 590),
        (420, 590),
        (462, 502),
        (516, 690),
        (566, 540),
        (606, 590),
        (702, 590),
    ]
    p.line(points, fill=(225, 29, 72, 255), width=34, joint="curve")
    for pt in (points[0], points[-1]):
        p.ellipse((pt[0] - 17, pt[1] - 17, pt[0] + 17, pt[1] + 17), fill=(225, 29, 72, 255))
    canvas.alpha_composite(pulse)

    icon = canvas.resize((FINAL, FINAL), Image.LANCZOS).convert("RGBA")
    icon.save(ASSETS / "app.png")

    sizes = [(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
    icon.save(ASSETS / "app.ico", format="ICO", sizes=sizes)
    print(f"yazıldı: {ASSETS / 'app.ico'} ve {ASSETS / 'app.png'}")


if __name__ == "__main__":
    main()
