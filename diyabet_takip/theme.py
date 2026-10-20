"""Arayüz teması: tutarlı renkler, fontlar ve bileşen fabrikaları.

v1'de her ekran kendi rastgele rengini/fontunu seçiyordu (Arial, teal/orange/
purple butonlar...). v2'de tek bir palete bağlandı.
"""

from __future__ import annotations

import tkinter as tk
from tkinter import scrolledtext, ttk

# --- Palet ---------------------------------------------------------------
APP_BG = "#f4f6f9"          # pencere arka planı
CARD_BG = "#ffffff"         # kart / panel
BORDER = "#d7dde5"          # kart kenarı

PRIMARY = "#0e7c86"         # ana marka (deniz mavisi)
PRIMARY_DARK = "#085b63"
PRIMARY_SOFT = "#e2f1f2"    # hover / seçili zemin

TEXT = "#1c2b33"
MUTED = "#64798a"

DANGER = "#b3261e"
DANGER_DARK = "#8c1d17"
SUCCESS = "#0e7f4b"
SUCCESS_DARK = "#0a5f38"

# Uyarı/bildirim satır zeminleri
CRITICAL_BG = "#fde8e8"
WARNING_BG = "#fff4d6"
NOTICE_BG = "#fdfbe6"
READ_BG = "#f1f3f5"

# --- Fontlar -------------------------------------------------------------
FONT_FAMILY = "Segoe UI"


def font(size: int, bold: bool = False) -> tuple:
    return (FONT_FAMILY, size, "bold" if bold else "normal")


# --- Bileşen fabrikaları --------------------------------------------------
def apply_theme(root: tk.Misc) -> None:
    """Pencere arka planı ve ttk stil tanımları."""
    root.configure(bg=APP_BG)
    style = ttk.Style()
    try:
        style.theme_use("clam")
    except tk.TclError:
        pass
    style.configure("TButton", font=font(10))
    style.configure("TNotebook.Tab", font=font(10, bold=True), padding=(14, 6))
    style.configure("Card.TFrame", background=CARD_BG)
    style.configure("Card.TLabelframe", background=CARD_BG, borderwidth=1)
    style.configure("Card.TLabelframe.Label", background=CARD_BG, font=font(11, True))


def frame(parent, card: bool = False, **kw) -> tk.Frame:
    kw.setdefault("bg", CARD_BG if card else APP_BG)
    if card:
        kw.setdefault("highlightbackground", BORDER)
        kw.setdefault("highlightthickness", 1)
    return tk.Frame(parent, **kw)


def title_label(parent, text: str, size: int = 16, fg=TEXT) -> tk.Label:
    return tk.Label(parent, text=text, font=font(size, True), bg=parent["bg"], fg=fg)


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


def button(parent, text: str, command, *, style: str = "primary", width: int | None = None) -> tk.Button:
    """Tutarlı buton fabrikası: primary / ghost / danger / success / neutral."""
    palettes = {
        "primary": (PRIMARY, "white", PRIMARY_DARK, PRIMARY_DARK),
        "success": (SUCCESS, "white", SUCCESS_DARK, SUCCESS_DARK),
        "danger": (DANGER, "white", DANGER_DARK, DANGER_DARK),
        "ghost": (CARD_BG, PRIMARY, PRIMARY_SOFT, PRIMARY_DARK),
        "neutral": ("#eef1f4", TEXT, "#dde3e8", TEXT),
    }
    bg, fg, active_bg, active_fg = palettes[style]
    kw = {
        "text": text,
        "command": command,
        "bg": bg,
        "fg": fg,
        "activebackground": active_bg,
        "activeforeground": active_fg,
        "font": font(10, style != "ghost"),
        "relief": "flat",
        "bd": 0,
        "cursor": "hand2",
        "padx": 14,
        "pady": 6,
        "highlightthickness": 1,
        "highlightbackground": bg,
    }
    if width:
        kw["width"] = width
    return tk.Button(parent, **kw)


def link_button(parent, text: str, command) -> tk.Button:
    return button(parent, text, command, style="ghost")


def entry(parent, width: int = 24, show: str | None = None) -> tk.Entry:
    kw = {
        "bg": "white",
        "fg": TEXT,
        "insertbackground": TEXT,
        "font": font(10),
        "relief": "flat",
        "highlightthickness": 1,
        "highlightbackground": BORDER,
        "highlightcolor": PRIMARY,
    }
    if show is not None:
        kw["show"] = show
    if width:
        kw["width"] = width
    return tk.Entry(parent, **kw)


def scrolled_text(parent, width: int = 80, height: int = 10) -> scrolledtext.ScrolledText:
    return scrolledtext.ScrolledText(
        parent,
        wrap=tk.WORD,
        width=width,
        height=height,
        font=font(10),
        bg=CARD_BG,
        fg=TEXT,
        relief="flat",
        highlightthickness=1,
        highlightbackground=BORDER,
        padx=8,
        pady=6,
    )

