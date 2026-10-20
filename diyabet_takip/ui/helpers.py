"""Ekran ortak yardımcıları: pencere oluşturma, form satırları, stil fabrikaları."""

from __future__ import annotations

import tkinter as tk

from .. import theme


def modal_window(parent, title: str, geometry: str, *, bg: str | None = None) -> tk.Toplevel:
    """Tutarlı Toplevel fabrikası (parent None → default root)."""
    win = tk.Toplevel(parent)
    win.title(title)
    if geometry:
        win.geometry(geometry)
    win.configure(bg=bg or theme.APP_BG)
    if parent is not None:
        win.transient(parent.winfo_toplevel())
    return win


def header(parent, text: str, subtitle: str = "") -> None:
    """Ekran başlığı + opsiyonel alt başlık."""
    top = theme.frame(parent)
    top.pack(fill="x", padx=16, pady=(16, 6))
    theme.title_label(top, text, 14).pack(anchor="w")
    if subtitle:
        theme.muted_label(top, subtitle, 9).pack(anchor="w", pady=(2, 0))


def form_row(parent, row: int, text: str, widget) -> None:
    """(Etiket + kontrol) grid satırı."""
    wrapper = theme.frame(parent)
    wrapper.grid(row=row, column=0, columnspan=2, sticky="ew", padx=10)
    parent.grid_columnconfigure(0, weight=1)
    theme.label(wrapper, text, 10).grid(row=0, column=0, sticky="w", pady=(8, 2))
    widget.grid(row=0, column=1, sticky="ew", padx=(6, 0))
    wrapper.grid_columnconfigure(1, weight=1)


def dropdown(parent, options, default: str | None = None, width: int = 18):
    """Tutarlı OptionMenu fabrikası. Dönen: (menu, var)."""
    var = tk.StringVar(parent)
    initial = default or (options[0] if options else "")
    var.set(initial)
    values = options if options else [""]
    menu = tk.OptionMenu(parent, var, *values)
    menu.config(
        width=width,
        font=theme.font(10),
        bg=theme.CARD_BG,
        fg=theme.TEXT,
        relief="flat",
    )
    if not options:
        menu.config(state="disabled")
    return menu, var


def info_panel(parent, text: str, icon: str | None = None) -> tk.Frame:
    """Boş liste / bilgi gösterimi."""
    box = theme.frame(parent, card=True)
    box.pack(expand=True, fill="both", padx=20, pady=20)
    label_text = f"{icon + '  ' if icon else ''}{text}"
    theme.muted_label(box, label_text, 10).pack(expand=True)
    return box


def date_label(dt) -> str:
    return dt.strftime("%d.%m.%Y") if dt else "—"


def datetime_label(dt) -> str:
    return dt.strftime("%d.%m.%Y %H:%M") if dt else "—"
