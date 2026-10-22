"""Arayüz teması: koyu palet, fontlar ve bileşen fabrikaları.

v2.2: uygulamanın tamamı koyu "dashboard" görünümüne geçti. Tüm ekranlar bu
paleti kullanır; butonlarda geometri değiştirmeyen (titremeyen) renk
animasyonları vardır.
"""

from __future__ import annotations

import tkinter as tk
from tkinter import font as tkfont
from tkinter import ttk

# --- Palet (koyu) ----------------------------------------------------------
APP_BG = "#0a0f1a"          # pencere arka planı (en koyu)
SIDEBAR_BG = "#070c16"      # sol menü (daha da koyu)
CARD_BG = "#111a2c"         # kart / panel
CARD_2 = "#1a2233"          # ikincil yüzey
CARD_HOVER = "#1b2740"      # kart hover zemini
BORDER = "#273350"          # kart kenarı
CARD_EDGE = "#2a3c62"       # cam kart / vurgulu kenar

PRIMARY = "#4f8cff"         # ana marka (mavi)
PRIMARY_DARK = "#2f6fe0"
PRIMARY_SOFT = "#152747"    # seçili zemin
CYAN = "#22d3ee"            # veri / vurgu

TEXT = "#e9edf7"
MUTED = "#93a1bd"

DANGER = "#ff6b6b"
DANGER_DARK = "#d64545"
SUCCESS = "#3ddc97"
SUCCESS_DARK = "#22a874"

# --- Aksan renkleri (fonksiyon bazlı) --------------------------------------
BLOOD = "#ff5f5f"           # kan şekeri — kırmızı
BLOOD_DARK = "#ff9a9a"
BLOOD_SOFT = "#3a1d26"

GREEN = "#4ade80"           # diyet
ORANGE = "#fb923c"          # egzersiz
PURPLE = "#c084fc"          # insülin
BLUE = "#60a5fa"
INDIGO = "#818cf8"
TEAL = "#2dd4bf"
AMBER = "#fbbf24"           # bildirim / bugün uyarı
SLATE = "#94a3b8"           # profil / nötr

# --- Karanlık yüzeyler -----------------------------------------------------
DARK_BG = APP_BG
DARK_BG_2 = "#12182a"
DARK_CARD = CARD_BG
DARK_BORDER = BORDER
DARK_FIELD = "#0f1626"
DARK_FIELD_BORDER = "#2d3b5c"
DARK_TEXT = TEXT
DARK_MUTED = MUTED
GRAD_A = "#3b82f6"          # gradient başlangıcı (mavi)
GRAD_B = "#6366f1"          # gradient bitişi (indigo)

# Uyarı/bildirim satır zeminleri (koyu varyantlar)
CRITICAL_BG = "#3b1d27"
WARNING_BG = "#3a311d"
NOTICE_BG = "#33301d"
READ_BG = "#1a2335"

# --- Fontlar -------------------------------------------------------------
FONT_FAMILY = "Segoe UI"


def font(size: int, bold: bool = False) -> tuple:
    return (FONT_FAMILY, size, "bold" if bold else "normal")


_DISPLAY_CANDIDATES = ("Segoe UI Variable Display Semib", "Segoe UI Semibold")
_display_family: str | None = None


def display(size: int) -> tuple:
    """Başlık fontu: Windows'ta yarı kalın Segoe ailesi varsa onu, yoksa kalın Segoe UI."""
    global _display_family
    if _display_family is None:
        try:
            available = set(tkfont.families())
        except tk.TclError:  # henüz Tk kökü yok: önbelleğe alma
            return (FONT_FAMILY, size, "bold")
        _display_family = next((name for name in _DISPLAY_CANDIDATES if name in available), "")
    if _display_family:
        return (_display_family, size)
    return (FONT_FAMILY, size, "bold")


# --- Renk yardımcıları -----------------------------------------------------
def _hex_to_rgb(c: str) -> tuple[int, int, int]:
    c = c.lstrip("#")
    return tuple(int(c[i : i + 2], 16) for i in (0, 2, 4))  # type: ignore[return-value]


def _blend(c1: str, c2: str, t: float) -> str:
    """İki renk arasında doğrusal geçiş; ``t`` 0 → c1, 1 → c2."""
    a, b = _hex_to_rgb(c1), _hex_to_rgb(c2)
    return "#{:02x}{:02x}{:02x}".format(
        *(round(x + (y - x) * t) for x, y in zip(a, b, strict=False))
    )


def mix(color: str, target: str, t: float) -> str:
    """``color``'u ``target`` yönünde ``t`` oranında karıştırır."""
    return _blend(color, target, t)


def dark_soft(accent: str, t: float = 0.22) -> str:
    """Aksan rengini koyu kart zeminiyle karıştırıp yumuşak zemin üretir."""
    return _blend(accent, CARD_BG, 1 - t)


# --- ttk stilleri -----------------------------------------------------------
def apply_theme(root: tk.Misc) -> None:
    """Koyu ttk stilleri (Treeview, scrollbar, notebook, sekme...)."""
    root.configure(bg=APP_BG)
    style = ttk.Style()
    try:
        style.theme_use("clam")
    except tk.TclError:
        pass

    style.configure(".", background=APP_BG, foreground=TEXT)
    style.configure("TFrame", background=APP_BG)
    style.configure("Card.TFrame", background=CARD_BG)
    style.configure("TLabel", background=APP_BG, foreground=TEXT)
    style.configure("TButton", font=font(10), padding=(12, 6))

    style.configure(
        "Treeview",
        background=CARD_BG,
        fieldbackground=CARD_BG,
        foreground=TEXT,
        rowheight=34,
        borderwidth=0,
        bordercolor=CARD_BG,
        lightcolor=CARD_BG,
        darkcolor=CARD_BG,
        relief="flat",
        font=font(10),
    )
    style.configure(
        "Treeview.Heading",
        background="#1c2740",
        foreground=MUTED,
        font=font(10, True),
        borderwidth=0,
        relief="flat",
        padding=(10, 9),
    )
    style.map(
        "Treeview",
        background=[("selected", PRIMARY_DARK)],
        foreground=[("selected", "white")],
    )
    style.map("Treeview.Heading", background=[("active", "#243254")])

    style.configure(
        "TNotebook",
        background=APP_BG,
        borderwidth=0,
        tabmargins=(2, 6, 2, 0),
        lightcolor=BORDER,
        darkcolor=BORDER,
        bordercolor=BORDER,
        focuscolor=APP_BG,
    )
    style.configure(
        "TNotebook.Tab",
        background=CARD_2,
        foreground=MUTED,
        padding=(18, 8),
        font=font(10, True),
        borderwidth=0,
        lightcolor=BORDER,
        darkcolor=BORDER,
        bordercolor=BORDER,
        focuscolor=CARD_BG,
    )
    style.map(
        "TNotebook.Tab",
        background=[("selected", CARD_BG), ("active", "#1f2a44")],
        foreground=[("selected", TEXT), ("active", TEXT)],
        lightcolor=[("selected", BORDER)],
        darkcolor=[("selected", BORDER)],
        bordercolor=[("selected", BORDER)],
        focuscolor=[("selected", CARD_BG)],
        padding=[("selected", (18, 8))],
    )
    # clam'ın seçili sekmede çizdiği beyaz odak halkasını kaldır.
    style.configure("Notebook.focus", focuscolor=CARD_BG, focusthickness=0)

    for orient in ("Vertical", "Horizontal"):
        style.configure(
            f"{orient}.TScrollbar",
            background="#2b3858",
            troughcolor=APP_BG,
            bordercolor=APP_BG,
            arrowcolor=MUTED,
            lightcolor=BORDER,
            darkcolor=BORDER,
        )
        style.map(f"{orient}.TScrollbar", background=[("active", PRIMARY_DARK)])

    style.configure("TCheckbutton", background=CARD_BG, foreground=TEXT)
    style.configure("TRadiobutton", background=CARD_BG, foreground=TEXT)
    style.configure(
        "TCombobox",
        fieldbackground=DARK_FIELD,
        background=CARD_2,
        foreground=TEXT,
        arrowcolor=MUTED,
        bordercolor=BORDER,
        lightcolor=BORDER,
        darkcolor=BORDER,
        padding=4,
    )
    style.map(
        "TCombobox",
        fieldbackground=[("readonly", DARK_FIELD), ("disabled", CARD_2)],
        foreground=[("readonly", TEXT), ("disabled", MUTED)],
        selectbackground=[("readonly", DARK_FIELD)],
        selectforeground=[("readonly", TEXT)],
        background=[("active", CARD_2)],
        arrowcolor=[("active", PRIMARY)],
    )
    style.configure(
        "TLabelframe",
        background=CARD_BG,
        foreground=TEXT,
        bordercolor=BORDER,
        lightcolor=BORDER,
        darkcolor=BORDER,
    )
    style.configure("TLabelframe.Label", background=CARD_BG, foreground=MUTED)


# --- Bileşen fabrikaları ---------------------------------------------------
def _sparkline(parent, values, color: str, width: int = 64, height: int = 30) -> tk.Canvas:
    """Mini trend grafiği (stat kartlarının sağında)."""
    canvas = tk.Canvas(
        parent, width=width, height=height, bg=CARD_BG,
        highlightthickness=0, bd=0,
    )
    nums = [float(v) for v in values if v is not None]
    if len(nums) < 2:
        return canvas
    lo, hi = min(nums), max(nums)
    span = (hi - lo) or 1.0
    pad = 3
    pts: list[float] = []
    for index, value in enumerate(nums):
        x = pad + index * (width - 2 * pad) / (len(nums) - 1)
        y = height - pad - (value - lo) / span * (height - 2 * pad)
        pts.extend((x, y))
    canvas.create_polygon(
        [*pts, width - pad, height - pad, pad, height - pad],
        fill=dark_soft(color, 0.30), outline="",
    )
    canvas.create_line(*pts, fill=color, width=1.8, smooth=True, splinesteps=12)
    return canvas


def stat_card(
    parent,
    *,
    icon: str,
    title: str,
    value,
    accent: str,
    pointer=None,
    spark: list | None = None,
    note: str | None = None,
):
    """Yuvarlatılmış metrik kartı: renkli rozet, başlık, büyük değer ve (varsa) sparkline."""
    from .ui import icons, surface  # döngüsel importu önlemek için lazy

    outer = surface.Panel(parent, radius=18, fill=CARD_BG, border=BORDER, pad=16, fit_width=False)
    body = outer.body
    row = tk.Frame(body, bg=CARD_BG)
    row.pack(fill="x")

    icons.badge(row, icon, accent, size=42, bg=CARD_BG).pack(side="left", anchor="n")

    text = tk.Frame(row, bg=CARD_BG)
    text.pack(side="left", padx=(12, 4), fill="x", expand=True)
    tk.Label(
        text,
        text=title,
        font=font(9),
        bg=CARD_BG,
        fg=MUTED,
        anchor="w",
        wraplength=160,
        justify="left",
    ).pack(anchor="w")
    tk.Label(
        text, text=str(value), font=display(20), bg=CARD_BG, fg=TEXT, anchor="w"
    ).pack(anchor="w", pady=(2, 0))
    if note:
        tk.Label(
            text, text=note, font=font(8, True), bg=CARD_BG, fg=accent, anchor="w"
        ).pack(anchor="w", pady=(3, 0))

    if spark:
        _sparkline(row, spark, accent, width=86, height=42).pack(side="right", anchor="s", padx=(2, 0))

    if pointer is not None:
        outer.grid(**pointer)
    return outer


def label(parent, text: str, size: int | None = None, *, bold: bool = False, fg=TEXT, **kw) -> tk.Label:
    kw.setdefault("bg", parent["bg"])
    kw.setdefault("fg", fg)
    if size is not None:
        kw["font"] = font(size, bold)
    elif bold:
        kw["font"] = font(10, True)
    return tk.Label(parent, text=text, **kw)


def muted_label(parent, text: str, size: int = 9, fg=MUTED, **kw) -> tk.Label:
    return label(parent, text, size=size, fg=fg, **kw)


_BUTTON_STYLE_MAP = {
    "primary": "primary",
    "success": "success",
    "danger": "danger",
    "ghost": "ghost",
    "neutral": "ghost",
}


def button(parent, text: str, command, *, style: str = "primary", width: int | None = None):
    """Yuvarlatılmış düğme. Hover'da yalnızca ton değişir; boyut sabit kalır.

    ``width`` geriye dönük uyumluluk için kabul edilir; genişlik metinden hesaplanır.
    """
    from .ui import surface  # döngüsel importu önlemek için lazy

    return surface.Button(
        parent, text, command, style=_BUTTON_STYLE_MAP.get(style, "primary"), height=38,
        font=font(10, True), bg=surface.bg_of(parent),
    )


def entry(parent, width: int = 24, show: str | None = None) -> tk.Entry:
    kw = {
        "bg": DARK_FIELD,
        "fg": TEXT,
        "insertbackground": TEXT,
        "font": font(10),
        "relief": "flat",
        "highlightthickness": 1,
        "highlightbackground": BORDER,
        "highlightcolor": PRIMARY,
        "disabledbackground": CARD_2,
        "disabledforeground": MUTED,
    }
    if show is not None:
        kw["show"] = show
    if width:
        kw["width"] = width
    return tk.Entry(parent, **kw)


def entry_with_unit(parent, unit: str, *, accent: str = BLOOD, width: int = 10) -> tk.Frame:
    """Değer kutusu + renkli birim rozeti (ör. mg/dL)."""
    row = tk.Frame(parent, bg=CARD_BG)
    ent = tk.Entry(
        row,
        font=font(12, True),
        fg=accent,
        bg=DARK_FIELD,
        insertbackground=accent,
        relief="flat",
        highlightthickness=1,
        highlightbackground=accent,
        highlightcolor=accent,
        width=width,
        justify="center",
    )
    ent.pack(side="left", ipady=4)
    tk.Label(
        row, text=unit, font=font(9, True),
        bg=accent, fg="#160a0a", padx=10, pady=5,
    ).pack(side="left", padx=(6, 0), fill="y")
    row.entry = ent
    return row


def date_entry(parent, width: int = 14):
    """Koyu temalı tkcalendar DateEntry (takvim açılırı da koyu)."""
    import tkcalendar

    return tkcalendar.DateEntry(
        parent,
        width=width,
        date_pattern="dd.mm.yyyy",
        firstweekday="sunday",
        background=DARK_FIELD,
        foreground=TEXT,
        normalbackground=CARD_BG,
        normalforeground=TEXT,
        weekendbackground=CARD_BG,
        weekendforeground=TEXT,
        othermonthbackground=APP_BG,
        othermonthforeground=MUTED,
        othermonthwebackground=APP_BG,
        othermonthweforeground=MUTED,
        headersbackground=CARD_2,
        headersforeground=TEXT,
        selectbackground=PRIMARY,
        selectforeground="white",
        bordercolor=BORDER,
        tooltipbackground=CARD_BG,
        tooltipforeground=TEXT,
    )


def spinbox(parent, **kw) -> tk.Spinbox:
    """Koyu temalı Spinbox (sayı girişleri)."""
    kw.setdefault("font", font(10))
    kw.setdefault("width", 10)
    kw.update(
        bg=DARK_FIELD,
        fg=TEXT,
        insertbackground=TEXT,
        buttonbackground=CARD_2,
        relief="flat",
        highlightthickness=1,
        highlightbackground=BORDER,
        highlightcolor=PRIMARY,
    )
    return tk.Spinbox(parent, **kw)


def listbox(parent, **kw) -> tk.Listbox:
    """Koyu temalı Listbox (çoklu seçim listeleri)."""
    kw.setdefault("font", font(10))
    kw.update(
        bg=DARK_FIELD,
        fg=TEXT,
        selectbackground=PRIMARY_DARK,
        selectforeground="white",
        relief="flat",
        highlightthickness=1,
        highlightbackground=BORDER,
        highlightcolor=PRIMARY,
    )
    return tk.Listbox(parent, **kw)
