"""Vektör ikonlar — Pillow ile süper örneklenmiş, anti-aliased render.

Tk Canvas'ın çizgi/çokgen ilkelleri kenar yumuşatma yapmaz (Windows'ta özellikle
küçük boyutlarda belirgin biçimde pikselli görünür). Bu modül ikon tariflerini
``draw()`` içinde ÖNCEKİ API ile (bir "canvas benzeri" nesne üzerinde
``create_line/create_polygon/create_oval/create_arc`` çağrıları) tanımlamaya
devam eder; ancak gerçek render ``_PILCanvas`` şimi üzerinden 4× büyük bir PIL
görüntüsüne yapılıp ardından LANCZOS ile küçültülür. Sonuç, Tk'ye şeffaf
(RGBA) ``PhotoImage`` olarak basılır; herhangi bir zeminle sorunsuz kaynaşır.
"""

from __future__ import annotations

import functools
import math
import pathlib
import tkinter as tk

from PIL import Image, ImageDraw, ImageFont, ImageTk

from .. import theme

_ASSETS = pathlib.Path(__file__).resolve().parents[2] / "assets"
_SS = 4  # süper örnekleme katsayısı

# İkon adları (dashboard ve sidebar tarafından kullanılır)
NAMES = {
    "home",
    "users",
    "user",
    "droplet",
    "syringe",
    "calendar",
    "pill",
    "report",
    "clipboard",
    "alert",
    "target",
    "chart",
    "trend",
    "clock",
    "bell",
    "heart",
    "stethoscope",
    "shield",
    "plus",
    "check",
    "folder",
    "bandage",
    "apple",
    "dumbbell",
    "logout",
    "settings",
    "arrow",
    "search",
    "menu",
    "spark",
    "refresh",
    "fullscreen",
    "mail",
    "eye",
    "eye_off",
}


def _pt(pts, x: float, y: float, s: float) -> list[float]:
    """0..1 normalize noktaları merkez (x, y), boyut s olacak şekilde ölçekler."""
    out: list[float] = []
    for px, py in pts:
        out.extend((x + (px - 0.5) * s, y + (py - 0.5) * s))
    return out


# --- PIL şim: tk.Canvas çizim API'sinin bir alt kümesi ----------------------
def _catmull_rom(p0, p1, p2, p3, t: float) -> tuple[float, float]:
    t2, t3 = t * t, t * t * t
    x = 0.5 * (
        2 * p1[0] + (-p0[0] + p2[0]) * t
        + (2 * p0[0] - 5 * p1[0] + 4 * p2[0] - p3[0]) * t2
        + (-p0[0] + 3 * p1[0] - 3 * p2[0] + p3[0]) * t3
    )
    y = 0.5 * (
        2 * p1[1] + (-p0[1] + p2[1]) * t
        + (2 * p0[1] - 5 * p1[1] + 4 * p2[1] - p3[1]) * t2
        + (-p0[1] + 3 * p1[1] - 3 * p2[1] + p3[1]) * t3
    )
    return (x, y)


def _smooth_points(pts: list[tuple[float, float]], steps: int = 12) -> list[tuple[float, float]]:
    """Tk'nin ``smooth=True`` kapalı çokgenine yakın bir Catmull-Rom eğrisi üretir."""
    n = len(pts)
    if n < 3:
        return pts
    out: list[tuple[float, float]] = []
    for i in range(n):
        p0, p1, p2, p3 = pts[(i - 1) % n], pts[i], pts[(i + 1) % n], pts[(i + 2) % n]
        for j in range(steps):
            out.append(_catmull_rom(p0, p1, p2, p3, j / steps))
    return out


class _PILCanvas:
    """``tk.Canvas.create_*`` imzalarının bir kısmını PIL ``ImageDraw`` üzerinde taklit eder.

    ``icons.draw()`` bu nesneyle çağrıldığında, mevcut ikon tarifleri hiç
    değişmeden süper örneklenmiş bir PIL görüntüsüne çizilir.
    """

    def __init__(self, draw: ImageDraw.ImageDraw, scale: int) -> None:
        self._d = draw
        self._s = scale

    def _scaled(self, *coords: float) -> list[float]:
        # Tk create_*, tek bir liste/tuple argümanı olarak da çağrılabilir
        # (ör. ``create_polygon(flat_list, **kw)``); burada düzleştirilir.
        if len(coords) == 1 and isinstance(coords[0], (list, tuple)):
            coords = coords[0]
        return [c * self._s for c in coords]

    def _width(self, width) -> int:
        return max(1, round(float(width or 1.0) * self._s))

    def create_line(self, *args, fill="black", width=1.0, capstyle=None,
                     joinstyle=None, smooth=None, splinesteps=None, **_kw) -> None:
        coords = self._scaled(*args)
        pts = list(zip(coords[0::2], coords[1::2], strict=True))
        w = self._width(width)
        if len(pts) >= 2:
            joint = "curve" if joinstyle == "round" and len(pts) > 2 else None
            self._d.line(pts, fill=fill, width=w, joint=joint)
        if capstyle == "round" and w > 1:
            r = w / 2
            for px, py in (pts[0], pts[-1]):
                self._d.ellipse((px - r, py - r, px + r, py + r), fill=fill)

    def create_polygon(self, *args, fill="", outline="", width=1.0, smooth=False,
                        splinesteps=12, joinstyle=None, **_kw) -> None:
        coords = self._scaled(*args)
        pts = list(zip(coords[0::2], coords[1::2], strict=True))
        if smooth:
            pts = _smooth_points(pts, splinesteps)
        fill_c = fill or None
        outline_c = outline or None
        w = self._width(width) if outline_c else 0
        # Pillow'un kendi outline çizimi köşeleri zaten makul biçimde birleştirir;
        # ek köşe noktası eklemek (create_line'daki gibi) keskin köşeli şekilleri
        # (ör. folder, alert) yuvarlak bir yumruya dönüştürür — burada eklenmez.
        self._d.polygon(pts, fill=fill_c, outline=outline_c, width=w or 1)

    def create_oval(self, x1, y1, x2, y2, *, outline="", width=1.0, fill="", **_kw) -> None:
        x1, y1, x2, y2 = self._scaled(x1, y1, x2, y2)
        if fill:
            self._d.ellipse((x1, y1, x2, y2), fill=fill)
        if outline:
            self._d.ellipse((x1, y1, x2, y2), outline=outline, width=self._width(width))

    def create_rectangle(self, x1, y1, x2, y2, *, outline="", width=1.0, fill="", **_kw) -> None:
        x1, y1, x2, y2 = self._scaled(x1, y1, x2, y2)
        if fill:
            self._d.rectangle((x1, y1, x2, y2), fill=fill)
        if outline:
            self._d.rectangle((x1, y1, x2, y2), outline=outline, width=self._width(width))

    def create_arc(self, x1, y1, x2, y2, *, start=0, extent=0, style="arc",
                    outline="", width=1.0, **_kw) -> None:
        x1, y1, x2, y2 = self._scaled(x1, y1, x2, y2)
        # Tk: 0°=doğu, pozitif açı GÖRSEL olarak saat yönünün TERSİNE (y aşağı
        # doğru olsa da matematik kuralına göre işaretlenir). PIL: 0°=doğu,
        # açı saat yönünde artar. pil_start = -(tk_start+tk_extent) (mod 360).
        pil_start = (-(start + extent)) % 360
        pil_end = pil_start + extent
        self._d.arc((x1, y1, x2, y2), pil_start, pil_end, fill=outline or None,
                    width=self._width(width))


def draw(c, name: str, x: float, y: float, size: float, color: str, width: float | None = None):
    """``c`` üzerine ``name`` ikonunu merkez (x, y) olacak şekilde çizer.

    ``c``, ``tk.Canvas`` veya ``_PILCanvas`` olabilir (aynı ``create_*`` imzaları).
    """
    if name not in NAMES:
        name = "spark"
    s = float(size)
    w = max(1.2, round(s * 0.09, 1)) if width is None else width
    line = {"fill": color, "width": w, "capstyle": "round", "joinstyle": "round"}
    fill = {"fill": color, "outline": ""}

    if name == "home":
        c.create_polygon(
            _pt([(0.5, 0.12), (0.1, 0.46), (0.2, 0.46), (0.2, 0.88),
                 (0.8, 0.88), (0.8, 0.46), (0.9, 0.46)], x, y, s),
            smooth=False, fill="", outline=color, width=w, joinstyle="round",
        )
        c.create_rectangle(*(x - 0.12 * s, y + 0.38 * s, x + 0.12 * s, y + 0.88 * s),
                           outline=color, width=w)

    elif name == "users":
        c.create_oval(*(x - 0.34 * s, y - 0.42 * s, x - 0.06 * s, y - 0.12 * s),
                      outline=color, width=w)
        c.create_arc(*(x - 0.46 * s, y + 0.02 * s, x + 0.06 * s, y + 0.52 * s),
                     start=0, extent=180, style="arc", outline=color, width=w)
        c.create_oval(*(x + 0.10 * s, y - 0.36 * s, x + 0.32 * s, y - 0.14 * s),
                      outline=color, width=w)
        c.create_arc(*(x + 0.04 * s, y - 0.02 * s, x + 0.44 * s, y + 0.38 * s),
                     start=0, extent=180, style="arc", outline=color, width=w)

    elif name == "user":
        c.create_oval(*(x - 0.18 * s, y - 0.42 * s, x + 0.18 * s, y - 0.06 * s),
                      outline=color, width=w)
        c.create_arc(*(x - 0.36 * s, y + 0.00 * s, x + 0.36 * s, y + 0.54 * s),
                     start=0, extent=180, style="arc", outline=color, width=w)

    elif name == "droplet":
        c.create_polygon(
            _pt([(0.5, 0.08), (0.86, 0.55), (0.82, 0.76), (0.66, 0.92),
                 (0.34, 0.92), (0.18, 0.76), (0.14, 0.55)], x, y, s),
            smooth=True, splinesteps=24, **fill,
        )
        c.create_oval(*(x - 0.10 * s, y + 0.28 * s, x + 0.02 * s, y + 0.44 * s),
                      fill=theme.mix(color, "#ffffff", 0.65), outline="")

    elif name == "syringe":
        c.create_rectangle(*(x - 0.30 * s, y - 0.10 * s, x + 0.20 * s, y + 0.10 * s),
                           outline=color, width=w)
        c.create_line(x - 0.46 * s, y, x - 0.30 * s, y, **line)
        c.create_line(x - 0.40 * s, y - 0.08 * s, x - 0.40 * s, y + 0.08 * s, **line)
        c.create_line(x + 0.20 * s, y, x + 0.46 * s, y, **line)
        for i in range(3):
            px = x - 0.16 * s + i * 0.10 * s
            c.create_line(px, y - 0.10 * s, px, y + 0.10 * s, fill=color, width=max(1, w - 0.6))

    elif name == "calendar":
        _rrect(c, x - 0.36 * s, y - 0.30 * s, x + 0.36 * s, y + 0.38 * s, 0.08 * s,
               fill="", outline=color, width=w)
        c.create_line(x - 0.36 * s, y - 0.10 * s, x + 0.36 * s, y - 0.10 * s, **line)
        c.create_line(x - 0.18 * s, y - 0.42 * s, x - 0.18 * s, y - 0.26 * s, **line)
        c.create_line(x + 0.18 * s, y - 0.42 * s, x + 0.18 * s, y - 0.26 * s, **line)
        for row in range(2):
            for col in range(3):
                cx = x - 0.20 * s + col * 0.20 * s
                cy = y + 0.06 * s + row * 0.16 * s
                c.create_oval(cx - 0.025 * s, cy - 0.025 * s, cx + 0.025 * s, cy + 0.025 * s,
                              fill=color, outline="")

    elif name == "pill":
        _rrect(c, x - 0.42 * s, y - 0.20 * s, x + 0.42 * s, y + 0.20 * s, 0.20 * s,
               fill="", outline=color, width=w)
        c.create_line(x, y - 0.20 * s, x, y + 0.20 * s, **line)

    elif name == "report":
        c.create_polygon(
            _pt([(0.24, 0.10), (0.62, 0.10), (0.78, 0.26), (0.78, 0.90),
                 (0.24, 0.90)], x, y, s),
            fill="", outline=color, width=w, joinstyle="round",
        )
        c.create_line(x + 0.12 * s, y - 0.24 * s, x + 0.12 * s, y - 0.10 * s,
                      x + 0.26 * s, y - 0.10 * s, **line)
        for i, frac in enumerate((0.02, 0.14, 0.26)):
            c.create_line(x - 0.16 * s, y + frac * s, x + (0.14 - i * 0.06) * s,
                          y + frac * s, fill=color, width=max(1, w - 0.5))

    elif name == "clipboard":
        _rrect(c, x - 0.30 * s, y - 0.36 * s, x + 0.30 * s, y + 0.40 * s, 0.07 * s,
               fill="", outline=color, width=w)
        _rrect(c, x - 0.16 * s, y - 0.46 * s, x + 0.16 * s, y - 0.30 * s, 0.05 * s,
               fill=theme.APP_BG, outline=color, width=w)
        for frac in (-0.10, 0.04, 0.18):
            c.create_line(x - 0.16 * s, y + frac * s, x + 0.16 * s, y + frac * s,
                          fill=color, width=max(1, w - 0.5))

    elif name == "alert":
        c.create_polygon(
            _pt([(0.5, 0.08), (0.94, 0.88), (0.06, 0.88)], x, y, s),
            fill="", outline=color, width=w, joinstyle="round",
        )
        c.create_line(x, y - 0.22 * s, x, y + 0.16 * s, **line)
        c.create_oval(x - 0.035 * s, y + 0.28 * s, x + 0.035 * s, y + 0.35 * s,
                      fill=color, outline="")

    elif name == "target":
        for r in (0.42, 0.26, 0.10):
            c.create_oval(*(x - r * s, y - r * s, x + r * s, y + r * s),
                          outline=color, width=w)
        c.create_oval(*(x - 0.045 * s, y - 0.045 * s, x + 0.045 * s, y + 0.045 * s),
                      fill=color, outline="")

    elif name == "chart":
        c.create_line(x - 0.40 * s, y - 0.42 * s, x - 0.40 * s, y + 0.38 * s, **line)
        c.create_line(x - 0.40 * s, y + 0.38 * s, x + 0.42 * s, y + 0.38 * s, **line)
        c.create_line(_pt([(0.18, 0.68), (0.38, 0.44), (0.56, 0.56), (0.82, 0.18)],
                          x, y, s), **line)

    elif name == "trend":
        c.create_line(_pt([(0.10, 0.72), (0.36, 0.48), (0.54, 0.60), (0.86, 0.24)],
                          x, y, s), **line)
        c.create_line(x + 0.22 * s, y - 0.26 * s, x + 0.36 * s, y - 0.26 * s,
                      x + 0.36 * s, y - 0.12 * s, **line)

    elif name == "clock":
        c.create_oval(*(x - 0.40 * s, y - 0.40 * s, x + 0.40 * s, y + 0.40 * s),
                      outline=color, width=w)
        c.create_line(x, y - 0.24 * s, x, y, x + 0.18 * s, y + 0.10 * s, **line)

    elif name == "bell":
        c.create_arc(*(x - 0.34 * s, y - 0.38 * s, x + 0.34 * s, y + 0.30 * s),
                     start=0, extent=180, style="arc", outline=color, width=w)
        c.create_line(x - 0.34 * s, y - 0.04 * s, x - 0.34 * s, y + 0.24 * s, **line)
        c.create_line(x + 0.34 * s, y - 0.04 * s, x + 0.34 * s, y + 0.24 * s, **line)
        c.create_line(x - 0.42 * s, y + 0.24 * s, x + 0.42 * s, y + 0.24 * s, **line)
        c.create_arc(*(x - 0.10 * s, y + 0.24 * s, x + 0.10 * s, y + 0.40 * s),
                     start=180, extent=180, style="arc", outline=color, width=w)

    elif name == "heart":
        c.create_oval(*(x - 0.40 * s, y - 0.32 * s, x - 0.01 * s, y + 0.08 * s),
                      **fill)
        c.create_oval(*(x + 0.01 * s, y - 0.32 * s, x + 0.40 * s, y + 0.08 * s),
                      **fill)
        c.create_polygon(_pt([(0.10, 0.38), (0.90, 0.38), (0.5, 0.86)], x, y, s),
                         fill=color, outline="")

    elif name == "stethoscope":
        c.create_line(*(x - 0.22 * s, y - 0.42 * s, x - 0.22 * s, y + 0.06 * s,
                        x + 0.10 * s, y + 0.34 * s, x + 0.30 * s, y + 0.10 * s,
                        x + 0.30 * s, y - 0.18 * s), **line)
        c.create_line(x - 0.30 * s, y - 0.42 * s, x - 0.14 * s, y - 0.42 * s, **line)
        c.create_line(x + 0.22 * s, y - 0.42 * s, x + 0.38 * s, y - 0.42 * s, **line)
        c.create_oval(*(x + 0.20 * s, y + 0.22 * s, x + 0.40 * s, y + 0.42 * s),
                      outline=color, width=w)

    elif name == "shield":
        c.create_polygon(
            _pt([(0.5, 0.06), (0.86, 0.22), (0.82, 0.62), (0.5, 0.92),
                 (0.18, 0.62), (0.14, 0.22)], x, y, s),
            smooth=True, splinesteps=20, fill="", outline=color, width=w,
        )
        c.create_line(_pt([(0.32, 0.50), (0.46, 0.64), (0.70, 0.34)], x, y, s), **line)

    elif name == "plus":
        c.create_line(x - 0.36 * s, y, x + 0.36 * s, y, width=w * 1.5,
                      fill=color, capstyle="round")
        c.create_line(x, y - 0.36 * s, x, y + 0.36 * s, width=w * 1.5,
                      fill=color, capstyle="round")

    elif name == "check":
        c.create_line(_pt([(0.16, 0.52), (0.40, 0.76), (0.84, 0.24)], x, y, s),
                      width=w * 1.4, fill=color, capstyle="round", joinstyle="round")

    elif name == "folder":
        c.create_polygon(
            _pt([(0.10, 0.26), (0.40, 0.26), (0.48, 0.36), (0.90, 0.36),
                 (0.90, 0.82), (0.10, 0.82)], x, y, s),
            fill="", outline=color, width=w, joinstyle="round",
        )
        c.create_line(x - 0.40 * s, y - 0.10 * s, x + 0.40 * s, y - 0.10 * s, **line)

    elif name == "bandage":
        c.create_line(x - 0.46 * s, y + 0.14 * s, x + 0.14 * s, y - 0.46 * s,
                      width=w * 2.2, fill=color, capstyle="round")
        for frac in (-0.18, 0.0, 0.18):
            c.create_oval(x + frac * s - 0.03 * s, y - frac * s - 0.03 * s,
                          x + frac * s + 0.03 * s, y - frac * s + 0.03 * s,
                          fill=theme.CARD_BG, outline="")

    elif name == "apple":
        c.create_oval(*(x - 0.36 * s, y - 0.24 * s, x + 0.36 * s, y + 0.44 * s),
                      outline=color, width=w)
        c.create_line(x, y - 0.26 * s, x + 0.06 * s, y - 0.48 * s, **line)
        c.create_polygon(_pt([(0.54, 0.10), (0.82, 0.02), (0.76, 0.26)], x, y, s),
                         fill=color, outline="")

    elif name == "dumbbell":
        c.create_line(x - 0.34 * s, y, x + 0.34 * s, y, width=w * 1.4, fill=color)
        for frac in (-0.46, -0.30, 0.30, 0.46):
            c.create_line(x + frac * s, y - 0.20 * s, x + frac * s, y + 0.20 * s,
                          width=w * 1.4, fill=color, capstyle="round")

    elif name == "logout":
        c.create_line(x + 0.06 * s, y - 0.42 * s, x - 0.34 * s, y - 0.42 * s,
                      x - 0.34 * s, y + 0.42 * s, x + 0.06 * s, y + 0.42 * s, **line)
        c.create_line(x - 0.06 * s, y, x + 0.40 * s, y, **line)
        c.create_line(x + 0.24 * s, y - 0.14 * s, x + 0.40 * s, y,
                      x + 0.24 * s, y + 0.14 * s, **line)

    elif name == "settings":
        c.create_oval(*(x - 0.16 * s, y - 0.16 * s, x + 0.16 * s, y + 0.16 * s),
                      outline=color, width=w)
        for i in range(8):
            ang = i * math.pi / 4
            c.create_line(
                x + math.cos(ang) * 0.26 * s, y + math.sin(ang) * 0.26 * s,
                x + math.cos(ang) * 0.42 * s, y + math.sin(ang) * 0.42 * s,
                width=w, fill=color, capstyle="round",
            )

    elif name == "arrow":
        c.create_line(x - 0.32 * s, y, x + 0.32 * s, y, **line)
        c.create_line(x + 0.10 * s, y - 0.18 * s, x + 0.32 * s, y,
                      x + 0.10 * s, y + 0.18 * s, **line)

    elif name == "search":
        c.create_oval(*(x - 0.34 * s, y - 0.38 * s, x + 0.20 * s, y + 0.16 * s),
                      outline=color, width=w)
        c.create_line(x + 0.14 * s, y + 0.12 * s, x + 0.38 * s, y + 0.38 * s, **line)

    elif name == "menu":
        for frac in (-0.24, 0.0, 0.24):
            c.create_line(x - 0.36 * s, y + frac * s, x + 0.36 * s, y + frac * s,
                          width=w, fill=color, capstyle="round")

    elif name == "refresh":
        c.create_arc(
            x - 0.36 * s, y - 0.36 * s, x + 0.36 * s, y + 0.36 * s,
            start=35, extent=285, style="arc", outline=color, width=w,
        )
        c.create_line(
            _pt([(0.56, 0.02), (0.82, 0.16), (0.62, 0.40)], x, y, s), **line
        )

    elif name == "fullscreen":
        for sx, sy in ((-1, -1), (1, -1), (-1, 1), (1, 1)):
            cx = x + sx * 0.36 * s
            cy = y + sy * 0.36 * s
            c.create_line(cx, cy, cx - sx * 0.20 * s, cy, **line)
            c.create_line(cx, cy, cx, cy - sy * 0.20 * s, **line)

    elif name == "mail":
        _rrect(c, x - 0.42 * s, y - 0.28 * s, x + 0.42 * s, y + 0.28 * s, 0.06 * s,
               fill="", outline=color, width=w)
        c.create_line(x - 0.42 * s, y - 0.24 * s, x, y + 0.06 * s,
                      x + 0.42 * s, y - 0.24 * s, **line)

    elif name in ("eye", "eye_off"):
        c.create_arc(*(x - 0.46 * s, y - 0.30 * s, x + 0.46 * s, y + 0.30 * s),
                     start=0, extent=180, style="arc", outline=color, width=w)
        c.create_arc(*(x - 0.46 * s, y - 0.30 * s, x + 0.46 * s, y + 0.30 * s),
                     start=180, extent=180, style="arc", outline=color, width=w)
        c.create_oval(*(x - 0.10 * s, y - 0.10 * s, x + 0.10 * s, y + 0.10 * s),
                      fill=color, outline="")
        if name == "eye_off":
            c.create_line(x - 0.38 * s, y + 0.34 * s, x + 0.38 * s, y - 0.34 * s,
                          width=w, fill=color, capstyle="round")

    else:  # spark
        c.create_line(_pt([(0.12, 0.62), (0.34, 0.40), (0.50, 0.54), (0.86, 0.18)],
                          x, y, s), **line)


def _rrect(c, x1, y1, x2, y2, r, **kw):
    """Yuvarlatılmış dikdörtgen (kapalı, yumuşatılmış çokgen)."""
    r = max(0, min(r, (x2 - x1) / 2, (y2 - y1) / 2))
    pts = [
        x1 + r, y1, x2 - r, y1, x2, y1, x2, y1 + r,
        x2, y2 - r, x2, y2, x2 - r, y2, x1 + r, y2,
        x1, y2, x1, y2 - r, x1, y1 + r, x1, y1,
    ]
    return c.create_polygon(pts, smooth=True, splinesteps=12, **kw)


def rounded_rect(c: tk.Canvas, x1, y1, x2, y2, r, **kw):
    """Dışa açık yuvarlatılmış dikdörtgen yardımcı (geriye dönük uyumluluk için)."""
    return _rrect(c, x1, y1, x2, y2, r, **kw)


# --- PIL render (anti-aliased, önbellekli) -----------------------------------
@functools.lru_cache(maxsize=1024)
def icon_image(name: str, size: int, color: str) -> Image.Image:
    """İkonu şeffaf (RGBA) PIL görüntüsü olarak üretir; 4× süper örnekleme + LANCZOS."""
    px = max(8, size)
    big = px * _SS
    img = Image.new("RGBA", (big, big), (0, 0, 0, 0))
    shim = _PILCanvas(ImageDraw.Draw(img), _SS)
    draw(shim, name, px / 2, px / 2, px * 0.82, color)
    return img.resize((px, px), Image.Resampling.LANCZOS)


@functools.lru_cache(maxsize=512)
def badge_image(
    name: str, color: str, size: int, bg: str, *, solid: bool = True, radius: int | None = None,
) -> Image.Image:
    """Renkli, yuvarlak köşeli rozet (opak PIL görüntüsü): zemin + kontrast ikon."""
    r = radius if radius is not None else max(8, round(size * 0.28))
    px = max(8, size)
    big = px * _SS
    rr = r * _SS
    fill_color = color if solid else theme.dark_soft(color, 0.30)
    img = Image.new("RGB", (big, big), bg)
    d = ImageDraw.Draw(img)
    if solid:
        d.rounded_rectangle((0, 0, big - 1, big - 1), radius=rr, fill=fill_color)
    else:
        d.rounded_rectangle((0, 0, big - 1, big - 1), radius=rr, fill=fill_color,
                            outline=color, width=_SS)
    img = img.resize((px, px), Image.Resampling.LANCZOS)
    icon_color = _contrast(color) if solid else color
    # icon_image kendi 0.82 iç oranını uygular; rozet içinde orantılı görünmesi
    # için ikonu rozetin ~%60'ı büyüklüğünde üretip ortalarız.
    inner = max(8, round(px * 0.60))
    icon = icon_image(name, inner, icon_color)
    offset = (px - inner) // 2
    img.paste(icon, (offset, offset), icon)
    return img


@functools.lru_cache(maxsize=1)
def _brand_source() -> Image.Image | None:
    path = _ASSETS / "app.png"
    if not path.exists():
        return None
    try:
        return Image.open(path).convert("RGBA")
    except OSError:
        return None


@functools.lru_cache(maxsize=1)
def _avatar_font_path() -> str | None:
    for candidate in (
        pathlib.Path(r"C:\Windows\Fonts\seguisb.ttf"),  # Segoe UI Semibold
        pathlib.Path(r"C:\Windows\Fonts\segoeuib.ttf"),  # Segoe UI Bold
    ):
        if candidate.exists():
            return str(candidate)
    return None


@functools.lru_cache(maxsize=256)
def avatar_image(initials: str, color: str, size: int) -> Image.Image:
    """Baş harfli, degrade halkalı yuvarlak avatar (RGBA, metin gömülü).

    ``ttk.Treeview`` gibi canlı bir Tk metnine izin vermeyen yerlerde kullanılır.
    """
    px = max(16, size)
    big = px * _SS
    img = Image.new("RGBA", (big, big), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    ring = max(2, round(big * 0.045))
    d.ellipse((ring, ring, big - ring, big - ring), fill=theme.dark_soft(color, 0.34),
             outline=color, width=ring)
    font_path = _avatar_font_path()
    text = (initials or "?")[:2].upper()
    font_size = round(big * 0.40)
    try:
        font = ImageFont.truetype(font_path, font_size) if font_path else ImageFont.load_default()
    except OSError:
        font = ImageFont.load_default()
    bbox = d.textbbox((0, 0), text, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    d.text((big / 2 - tw / 2 - bbox[0], big / 2 - th / 2 - bbox[1]), text, fill=color, font=font)
    return img.resize((px, px), Image.Resampling.LANCZOS)


def icon(parent, name: str, *, size: int = 22, color: str = theme.TEXT, bg: str | None = None) -> tk.Canvas:
    """Tek başına duran, şeffaf zeminli, anti-aliased ikon canvas'ı."""
    if bg is None:
        try:
            bg = parent["bg"]
        except tk.TclError:
            bg = theme.APP_BG
    canvas = tk.Canvas(parent, width=size, height=size, bg=bg, highlightthickness=0, bd=0)
    photo = ImageTk.PhotoImage(icon_image(name, size, color))
    canvas.create_image(0, 0, anchor="nw", image=photo)
    canvas._icon_image = photo  # GC'ye karşı referans
    return canvas


def _contrast(color: str) -> str:
    r, g, b = theme._hex_to_rgb(color)
    lum = (0.299 * r + 0.587 * g + 0.114 * b) / 255
    return "#0a0f1a" if lum > 0.62 else "#ffffff"


def badge(
    parent, name: str, color: str, *, size: int = 42, bg: str | None = None,
    solid: bool = True, radius: int | None = None,
) -> tk.Canvas:
    """Renkli rozet: solid zemin + kontrast ikon (dashboard kartları)."""
    if bg is None:
        try:
            bg = parent["bg"]
        except tk.TclError:
            bg = theme.CARD_BG
    canvas = tk.Canvas(parent, width=size, height=size, bg=bg, highlightthickness=0, bd=0)
    photo = ImageTk.PhotoImage(badge_image(name, color, size, bg, solid=solid, radius=radius))
    canvas.create_image(0, 0, anchor="nw", image=photo)
    canvas._badge_image = photo  # GC'ye karşı referans
    return canvas


def brand_image(size: int = 36) -> ImageTk.PhotoImage | None:
    """Uygulama ikonunu marka işareti olarak döndürür (LANCZOS, anti-aliased).

    Önceki sürüm Tk'nin ``subsample()``'ını kullanıyordu (piksel atlayarak
    küçültür, belirgin biçimde pikselli/bulanık görünür). Kaynak PNG PIL
    düzeyinde önbelleğe alınır; dönen ``PhotoImage`` kök pencereye bağlı
    olduğundan her çağrıda yeniden oluşturulur.
    """
    src = _brand_source()
    if src is None:
        return None
    resized = src.resize((size, size), Image.Resampling.LANCZOS)
    return ImageTk.PhotoImage(resized)
