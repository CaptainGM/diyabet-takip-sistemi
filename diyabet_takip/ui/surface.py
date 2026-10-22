"""Anti-aliased yüzeyler: yuvarlatılmış kartlar, düğmeler ve arka planlar.

Tk'nin Canvas'ı köşe yuvarlatma ve kısmi saydamlık sunmaz. Şekiller Pillow ile
4 kat büyük çizilip küçültülerek üretilir (kenarlar yumuşar). Sonuçlar önbelleğe
alınır: kart yeniden boyutlandığında yalnızca köşe parçaları taşınır, görüntü
yeniden çizilmez.
"""

from __future__ import annotations

import functools
import math
import tkinter as tk
from tkinter import font as tkfont

from PIL import Image, ImageDraw, ImageFilter, ImageOps, ImageTk

from .. import theme

SS = 4  # süper örnekleme katsayısı (kenar yumuşatma)
LANCZOS = Image.Resampling.LANCZOS


def _rgb(color: str) -> tuple[int, int, int]:
    return theme._hex_to_rgb(color)


def bg_of(widget) -> str:
    try:
        return widget["bg"]
    except tk.TclError:
        return theme.APP_BG


def lighten(color: str, amount: float = 0.12) -> str:
    return theme.mix(color, "#ffffff", amount)


def _solid(w: int, h: int, color: str) -> Image.Image:
    return Image.new("RGB", (w, h), _rgb(color))


def _gradient(w: int, h: int, c1: str, c2: str, vertical: bool = False) -> Image.Image:
    if c1 == c2 or w < 1 or h < 1:
        return _solid(w, h, c1)
    img = Image.new("RGB", (w, h))
    draw = ImageDraw.Draw(img)
    steps = h if vertical else w
    span = max(steps - 1, 1)
    for i in range(steps):
        color = _rgb(theme._blend(c1, c2, i / span))
        if vertical:
            draw.line((0, i, w, i), fill=color)
        else:
            draw.line((i, 0, i, h), fill=color)
    return img


@functools.lru_cache(maxsize=256)
def _mask(w: int, h: int, radius: int) -> Image.Image:
    """Yuvarlatılmış dikdörtgenin anti-aliased maskesi (önbellekli, salt okunur)."""
    radius = max(0, min(radius, w // 2, h // 2))
    big = Image.new("L", (w * SS, h * SS), 0)
    ImageDraw.Draw(big).rounded_rectangle(
        (0, 0, w * SS - 1, h * SS - 1), radius=radius * SS, fill=255
    )
    return big.resize((w, h), LANCZOS)


def _inner_mask(w: int, h: int, radius: int, inset: int) -> Image.Image:
    inner = Image.new("L", (w, h), 0)
    inner.paste(_mask(w - 2 * inset, h - 2 * inset, max(radius - inset, 0)), (inset, inset))
    return inner


@functools.lru_cache(maxsize=256)
def _surface(
    w: int,
    h: int,
    radius: int,
    fill: str,
    fill2: str | None,
    border: str | None,
    bg: str,
    vertical: bool,
) -> Image.Image:
    """Dış kenarı ``bg``, içi (isteğe bağlı gradyanlı) ``fill``, kenarı ``border`` olan görüntü."""
    base = _solid(w, h, bg)
    outer = _mask(w, h, radius)
    if border:
        base.paste(_solid(w, h, border), (0, 0), outer)
        inner = _inner_mask(w, h, radius, 1)
    else:
        inner = outer
    base.paste(_gradient(w, h, fill, fill2 or fill, vertical), (0, 0), inner)
    return base


def composite_card_image(
    background: Image.Image, radius: int, fill: str, border: str | None = None
) -> Image.Image:
    """Düz dolgulu kartı, altındaki arka plan kırpımının üzerine oturtur (PIL).

    Köşelerin dış kısmı arka planın kendisi olduğu için (ör. giriş ekranındaki
    ışık lekeli zemin) kart kenarında renk farkı kalmaz. Dönen görüntüye bir
    ikon (``icon_image`` ile üretilmiş, RGBA) eklemek için çağıran taraf
    ``Image.paste(icon, (x, y), icon)`` kullanabilir.
    """
    w, h = background.size
    base = background.convert("RGB")
    outer = _mask(w, h, radius)
    if border:
        base.paste(_solid(w, h, border), (0, 0), outer)
        inner = _inner_mask(w, h, radius, 1)
    else:
        inner = outer
    base.paste(_solid(w, h, fill), (0, 0), inner)
    return base


def composite_card(
    background: Image.Image, radius: int, fill: str, border: str | None = None
) -> ImageTk.PhotoImage:
    """``composite_card_image``'in Tk ``PhotoImage`` sarmalayıcısı."""
    return ImageTk.PhotoImage(composite_card_image(background, radius, fill, border))


@functools.lru_cache(maxsize=512)
def rounded_image(
    w: int,
    h: int,
    radius: int,
    fill: str,
    *,
    fill2: str | None = None,
    border: str | None = None,
    bg: str | None = None,
    vertical: bool = False,
) -> Image.Image:
    """Yuvarlatılmış düğme/çip/kart zemini (PIL, önbellekli).

    Önbellekte Tk görüntüsü tutulmaz: Tk görüntüleri kök pencereye bağlıdır ve
    pencere yeniden oluşturulunca geçersiz kalır. Widget, ``ImageTk.PhotoImage``
    ile kendi kopyasını oluşturup saklar.
    """
    return _surface(w, h, radius, fill, fill2, border, bg or theme.APP_BG, vertical)


@functools.lru_cache(maxsize=128)
def card_corners(radius: int, fill: str, border: str | None, bg: str) -> tuple[Image.Image, ...]:
    """Kart köşeleri (PIL): tek çeyrek üretilir, diğer üçü aynalanır."""
    size = radius * 2
    top_left = _surface(size, size, radius, fill, None, border, bg, False).crop(
        (0, 0, radius, radius)
    )
    return (
        top_left,
        top_left.transpose(Image.Transpose.FLIP_LEFT_RIGHT),
        top_left.transpose(Image.Transpose.FLIP_TOP_BOTTOM),
        top_left.transpose(Image.Transpose.ROTATE_180),
    )


class Panel(tk.Canvas):
    """Yuvarlatılmış köşeli, ince kenarlı yüzey.

    İçerik ``panel.body`` çerçevesine yerleştirilir; kart, içeriği kadar
    büyür. Köşeler önbellekten gelir, yeniden boyutlandırma yalnızca taşır.
    """

    def __init__(
        self,
        parent,
        *,
        radius: int = 16,
        fill: str | None = None,
        border: str | None = None,
        pad: int = 16,
        bg: str | None = None,
        height: int | None = None,
        fit_width: bool = True,
    ) -> None:
        self.radius = radius
        self.pad = pad
        self._fill = fill or theme.CARD_BG
        self._border = theme.BORDER if border is None else border
        self._bg = bg or bg_of(parent)
        self._height = height  # verilirse kart bu yüksekliği korur (içerik kayabilir)
        # False: genişliği içerik değil, yerleştiren geometri yöneticisi belirler (grid).
        self._fit_width = fit_width
        extra = {"height": height} if height else {}
        super().__init__(parent, bg=self._bg, highlightthickness=0, bd=0, **extra)

        self._fill_item = self.create_rectangle(0, 0, 1, 1, fill=self._fill, outline="")
        self._corner_items = [self.create_image(0, 0, anchor="nw") for _ in range(4)]
        self._edge_items = [
            self.create_rectangle(0, 0, 1, 1, fill=self._fill, outline="") for _ in range(4)
        ]
        self.body = tk.Frame(self, bg=self._fill, highlightthickness=0, bd=0)
        self._window = self.create_window(pad, pad, window=self.body, anchor="nw")
        self._paint()
        self.bind("<Configure>", self._layout)
        self.body.bind("<Configure>", self._fit)

    def _paint(self) -> None:
        self._corners = tuple(
            ImageTk.PhotoImage(image)
            for image in card_corners(self.radius, self._fill, self._border, self._bg)
        )
        for item, image in zip(self._corner_items, self._corners, strict=True):
            self.itemconfigure(item, image=image)
        edge = self._border or self._fill
        self.itemconfigure(self._fill_item, fill=self._fill)
        for item in self._edge_items:
            self.itemconfigure(item, fill=edge)
        self.body.configure(bg=self._fill)
        self._layout()

    def _layout(self, _event=None) -> None:
        w, h, r = self.winfo_width(), self.winfo_height(), self.radius
        if w <= 2 * r or h <= 2 * r:
            return
        self.coords(self._fill_item, 0, 0, w, h)
        top_left, top_right, bottom_left, bottom_right = self._corner_items
        self.coords(top_left, 0, 0)
        self.coords(top_right, w - r, 0)
        self.coords(bottom_left, 0, h - r)
        self.coords(bottom_right, w - r, h - r)
        top, bottom, left, right = self._edge_items
        self.coords(top, r, 0, w - r, 1)
        self.coords(bottom, r, h - 1, w - r, h)
        self.coords(left, 0, r, 1, h - r)
        self.coords(right, w - 1, r, w, h - r)
        self.itemconfigure(self._window, width=max(1, w - 2 * self.pad))
        if self._height:
            self.itemconfigure(self._window, height=max(1, h - 2 * self.pad))
        self.coords(self._window, self.pad, self.pad)

    def _fit(self, _event=None) -> None:
        height = self._height or self.body.winfo_reqheight() + 2 * self.pad
        width = self.body.winfo_reqwidth() + 2 * self.pad if self._fit_width else 1
        self.configure(width=width, height=height)

    def set_border(self, color: str | None) -> None:
        """Yalnızca kenar rengini değiştirir (odak / hover vurgusu)."""
        self._border = color
        self._paint()

    def set_fill(self, color: str) -> None:
        """Dolgu rengini değiştirir (gezinme öğesi seçimi / hover)."""
        self._fill = color
        self._paint()


_BUTTON_STYLES: dict[str, dict] = {
    "primary": {
        "fill": theme.GRAD_A, "fill2": theme.GRAD_B, "border": None, "fg": "#ffffff",
    },
    "success": {
        "fill": theme.SUCCESS_DARK, "fill2": theme.SUCCESS, "border": None, "fg": "#04140c",
    },
    "danger": {
        "fill": theme.DANGER_DARK, "fill2": theme.DANGER, "border": None, "fg": "#ffffff",
    },
    "ghost": {
        "fill": theme.CARD_2, "fill2": None, "border": theme.BORDER, "fg": theme.TEXT,
    },
    "chip": {
        "fill": theme.CARD_2, "fill2": None, "border": theme.BORDER, "fg": theme.MUTED,
    },
    "chip_on": {
        "fill": theme.GRAD_A, "fill2": theme.GRAD_B, "border": None, "fg": "#ffffff",
    },
}


class Button(tk.Canvas):
    """Yuvarlatılmış düğme veya çip. Hover'da yalnızca ton değişir; boyut sabit kalır."""

    def __init__(
        self,
        parent,
        text: str,
        command,
        *,
        style: str = "primary",
        height: int = 44,
        radius: int | None = None,
        font: tuple | None = None,
        bg: str | None = None,
        padx: int = 22,
    ) -> None:
        self._bg = bg or bg_of(parent)
        self._spec = _BUTTON_STYLES[style]
        self._radius = radius
        self._command = command
        self._hover = False
        self._image = None
        font = font or theme.font(10, True)
        # Tk canvas varsayılan genişliği ~378 px; düğmeyi metnine göre boyutlandır.
        width = tkfont.Font(font=font).measure(text) + 2 * padx
        super().__init__(
            parent, width=width, height=height, bg=self._bg,
            highlightthickness=0, bd=0, cursor="hand2",
        )
        self._image_item = self.create_image(0, 0, anchor="nw")
        self._text_item = self.create_text(
            0, 0, text=text, fill=self._spec["fg"], font=font
        )
        self.bind("<Configure>", self._draw)
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        self.bind("<Button-1>", self._on_click)

    def _colors(self) -> tuple[str, str | None, str | None]:
        spec = self._spec
        if not self._hover:
            return spec["fill"], spec["fill2"], spec["border"]
        fill = lighten(spec["fill"], 0.10)
        fill2 = lighten(spec["fill2"], 0.10) if spec["fill2"] else None
        return fill, fill2, spec["border"]

    def _draw(self, _event=None) -> None:
        w, h = self.winfo_width(), self.winfo_height()
        if w < 4 or h < 4:
            return
        fill, fill2, border = self._colors()
        radius = self._radius if self._radius is not None else min(w, h) // 2
        self._image = ImageTk.PhotoImage(
            rounded_image(w, h, radius, fill, fill2=fill2, border=border, bg=self._bg)
        )
        self.itemconfigure(self._image_item, image=self._image)
        self.itemconfigure(self._text_item, fill=self._spec["fg"])
        self.coords(self._text_item, w // 2, h // 2)

    def set_text(self, text: str) -> None:
        self.itemconfigure(self._text_item, text=text)

    def configure(self, cnf=None, **kw):
        """``text`` ve ``command`` tk.Button ile aynı adlarla değiştirilebilir."""
        if "text" in kw:
            self.set_text(kw.pop("text"))
        if "command" in kw:
            self._command = kw.pop("command")
        if cnf or kw:
            return super().configure(cnf, **kw)
        return None

    config = configure

    def set_active(self, on: bool) -> None:
        """Çipleri seçili/değil durumuna çevirir (stil değişimi)."""
        self._spec = _BUTTON_STYLES["chip_on" if on else "chip"]
        self.itemconfigure(self._text_item, fill=self._spec["fg"])
        self._draw()

    def _on_enter(self, _event=None) -> None:
        self._hover = True
        self._draw()

    def _on_leave(self, _event=None) -> None:
        self._hover = False
        self._draw()

    def _on_click(self, _event=None) -> None:
        if self._command is not None:
            self._command()


class Avatar(tk.Canvas):
    """Baş harflerden oluşan yuvarlak rozet."""

    def __init__(self, parent, initials: str, color: str, *, size: int = 36, bg=None) -> None:
        bg = bg or bg_of(parent)
        super().__init__(parent, width=size, height=size, bg=bg, highlightthickness=0, bd=0)
        self._image = ImageTk.PhotoImage(
            rounded_image(size, size, size // 2, theme.dark_soft(color, 0.34), bg=bg)
        )
        self.create_image(0, 0, anchor="nw", image=self._image)
        self.create_text(
            size // 2, size // 2, text=initials, fill=color,
            font=theme.font(max(8, size // 4), True),
        )


def hero_banner_image(w: int, h: int, path: str, radius: int, bg: str) -> Image.Image:
    """Fotoğraflı karşılama şeridi (PIL): sağa hizalı kırpma, yuvarlatılmış köşeler."""
    photo = Image.open(path).convert("RGB")
    fitted = ImageOps.fit(photo, (w, h), method=LANCZOS, centering=(1.0, 0.5))
    base = _solid(w, h, bg)
    base.paste(fitted, (0, 0), _mask(w, h, radius))
    return base


def hero_banner(w: int, h: int, path: str, radius: int, bg: str) -> ImageTk.PhotoImage:
    """``hero_banner_image``'in Tk ``PhotoImage`` sarmalayıcısı."""
    return ImageTk.PhotoImage(hero_banner_image(w, h, path, radius, bg))


# --- Arka plan kompozisyonu (giriş ekranı) -----------------------------------
# (merkez x, merkez y, yarıçap x, yarıçap y, renk, yoğunluk) — 0..1 oranları
_GLOWS = (
    (0.10, 0.18, 0.55, 0.60, theme.PRIMARY, 0.55),
    (0.92, 0.08, 0.42, 0.46, theme.INDIGO, 0.34),
    (0.18, 0.98, 0.50, 0.48, theme.CYAN, 0.18),
    (0.86, 0.92, 0.46, 0.50, theme.PRIMARY, 0.22),
)


def _radial_mask(w: int, h: int) -> Image.Image:
    """Merkezde 255, elipsin dışında 0 olan doğrusal düşüşlü maske.

    Halkalar dıştan içe çizilir; ``Image.radial_gradient`` gibi kenarda doygunluk
    (sert sınır) oluşmaz.
    """
    w, h = max(w, 2), max(h, 2)
    mask = Image.new("L", (w, h), 0)
    draw = ImageDraw.Draw(mask)
    cx, cy = w / 2, h / 2
    steps = 160
    for i in range(steps):
        t = 1 - i / steps  # 1: dış halka, 0: merkez
        rx, ry = cx * t, cy * t
        draw.ellipse((cx - rx, cy - ry, cx + rx, cy + ry), fill=round(255 * (1 - t)))
    return mask


def _glow(canvas: Image.Image, cx: float, cy: float, rx: float, ry: float, color: str, power: float) -> Image.Image:
    w, h = canvas.size
    gw, gh = max(int(2 * rx), 2), max(int(2 * ry), 2)
    mask = _radial_mask(gw, gh).point(lambda v: int(255 * (v / 255) ** 2.2 * power))
    full = Image.new("L", (w, h), 0)
    full.paste(mask, (int(cx - rx), int(cy - ry)))
    return Image.composite(_solid(w, h, color), canvas, full)


def _ecg(canvas: Image.Image, y: float, x0: float, x1: float, amp: float, color: str) -> Image.Image:
    """Yumuşak parıltılı EKG çizgisi (dekoratif)."""
    w, h = canvas.size
    beat = max((x1 - x0) / 9.0, 20.0)
    points: list[tuple[float, float]] = []
    x = x0
    while x <= x1:
        phase = ((x - x0) % beat) / beat
        dy = 0.0
        if 0.30 < phase < 0.36:
            dy = -0.18 * math.sin((phase - 0.30) / 0.06 * math.pi)
        elif 0.40 < phase < 0.44:
            dy = 0.10 * math.sin((phase - 0.40) / 0.04 * math.pi)
        elif 0.46 < phase < 0.52:
            dy = 1.0 * math.sin((phase - 0.46) / 0.06 * math.pi)
        elif 0.52 < phase < 0.56:
            dy = -0.22 * math.sin((phase - 0.52) / 0.04 * math.pi)
        points.append((x, y - dy * amp))
        x += 3
    mask = Image.new("L", (w, h), 0)
    ImageDraw.Draw(mask).line(points, fill=255, width=7, joint="curve")
    glow = mask.filter(ImageFilter.GaussianBlur(7)).point(lambda v: int(v * 0.45))
    canvas = Image.composite(_solid(w, h, color), canvas, glow)
    line = Image.new("L", (w, h), 0)
    ImageDraw.Draw(line).line(points, fill=255, width=2, joint="curve")
    return Image.composite(_solid(w, h, color), canvas, line.point(lambda v: int(v * 0.85)))


@functools.lru_cache(maxsize=4)
def backdrop_image(w: int, h: int) -> Image.Image:
    """Giriş ekranı arka planı (PIL): lacivert gradyan, ışık lekeleri, EKG çizgisi.

    Yarı çözünürlükte hesaplanıp büyütülür; yumuşak ışıklarda kalite kaybı yoktur
    ama pencere yeniden boyutlandığında maliyet dört kat düşer.
    """
    sw, sh = max(w // 2, 2), max(h // 2, 2)
    base = _gradient(sw, sh, "#05091a", "#0a1834", vertical=True)
    for fx, fy, frx, fry, color, power in _GLOWS:
        base = _glow(base, fx * sw, fy * sh, frx * sw, fry * sh, color, power)
    base = _ecg(base, sh * 0.80, sw * 0.04, sw * 0.60, sh * 0.05, theme.CYAN)
    vignette = _radial_mask(sw, sh).point(lambda v: int((255 - v) * 0.55))
    base = Image.composite(_solid(sw, sh, "#03060f"), base, vignette)
    return base.resize((w, h), LANCZOS)
