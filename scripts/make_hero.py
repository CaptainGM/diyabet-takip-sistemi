"""Hero banner görselini üretir (assets/hero-klinik.png).

Sol tarafta başlık metni için koyu lacivert gradyan, sağ tarafta modern
klinik ortamında tabletiyle hasta verilerini inceleyen bir doktor. Kaynak
fotoğraf Pexels #5452293 (ücretsiz kullanım lisansı); indirilemezse aynı
paletle soyut bir banner üretilir.
"""

from __future__ import annotations

import math
import pathlib
import urllib.request

from PIL import Image, ImageDraw, ImageFilter

ROOT = pathlib.Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"
OUT = ASSETS / "hero-klinik.png"
SOURCE_URL = (
    "https://images.pexels.com/photos/5452293/pexels-photo-5452293.jpeg"
    "?auto=compress&cs=tinysrgb&w=1600"
)
W, H = 1600, 200
NAVY = (7, 13, 26)


def _base() -> Image.Image:
    """Lacivert gradyan + yumuşak aurora + ince ECG çizgileri."""
    img = Image.new("RGB", (W, H), NAVY)
    d = ImageDraw.Draw(img)
    for x in range(W):
        t = x / max(W - 1, 1)
        d.line(
            [(x, 0), (x, H)],
            fill=(round(8 + 6 * t), round(14 + 10 * t), round(28 + 18 * t)),
        )

    glow = Image.new("RGB", (W, H), NAVY)
    gd = ImageDraw.Draw(glow)
    gd.ellipse((W * 0.55, -H * 0.8, W * 1.1, H * 1.2), fill=(14, 44, 82))
    gd.ellipse((-W * 0.15, H * 0.2, W * 0.45, H * 1.6), fill=(48, 28, 96))
    glow = glow.filter(ImageFilter.GaussianBlur(120))
    img = Image.blend(img, glow, 0.34)

    for k in range(3):
        y0 = H * (0.55 + 0.13 * k)
        pts = []
        for x in range(0, W, 4):
            t = x / W
            spike = 70 if int(t * 60 + k * 20) % 20 == 4 else 0
            pts.append((x, y0 + 18 * math.sin(t * 8 + k) + spike))
        d.line(pts, fill=(26, 66, 108), width=1)
    return img


def _fallback() -> Image.Image:
    return _base()


def _download() -> Image.Image | None:
    try:
        req = urllib.request.Request(
            SOURCE_URL,
            headers={
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/124.0 Safari/537.36"
                )
            },
        )
        raw = urllib.request.urlopen(req, timeout=60).read()
        tmp = ASSETS / "_hero-source.jpg"
        tmp.write_bytes(raw)
        src = Image.open(tmp).convert("RGB")
        tmp.unlink(missing_ok=True)
        return src
    except Exception as exc:
        print(f"Kaynak indirilemedi ({exc}); soyut banner kullanılacak.")
        return None


def _paste_doctor(base: Image.Image, src: Image.Image) -> Image.Image:
    """Doktorun baş/omuz bölümünü sağ tarafa, solda şeffaflaşarak yerleştir."""
    # Kaynak 1600x2400; baş + yaka + stetoskopu kapsayan üst gövde kesiti.
    crop = src.crop((200, 80, 1400, 1180)).resize((218, 200), Image.LANCZOS)
    crop = Image.blend(crop, Image.new("RGB", crop.size, (10, 20, 38)), 0.18)

    mask = Image.new("L", crop.size, 255)
    mp = mask.load()
    assert mp is not None
    for x in range(crop.width):
        for y in range(crop.height):
            alpha = 255 * min(1.0, x / 80)
            if y < 22:
                alpha *= y / 22
            if y > crop.height - 30:
                alpha *= (crop.height - y) / 30
            mp[x, y] = round(alpha)

    base.paste(crop, (W - crop.width, 0), mask)
    # Sağ alt köşeye hafif karartma (kart kenarına yumuşak geçiş).
    shade = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    sd = ImageDraw.Draw(shade)
    sd.rectangle((W - 260, H - 110, W, H), fill=(7, 13, 26, 90))
    shade = shade.filter(ImageFilter.GaussianBlur(40))
    return Image.alpha_composite(base.convert("RGBA"), shade).convert("RGB")


def build() -> None:
    ASSETS.mkdir(exist_ok=True)
    img = _base()
    src = _download()
    if src is not None:
        img = _paste_doctor(img, src)
    img.save(OUT, optimize=True)
    print(f"yazıldı: {OUT} ({OUT.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    build()
