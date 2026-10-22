"""Tek pencere çalışma alanı için ortak sayfa bileşenleri.

v2.4: Sol menüdeki ekranlar artık ayrı Toplevel pencereler değil; ana kabuğun
içindeki sayfalardır. Bu modül sayfaların ortak başlık, kart, metrik, tablo ve
form bileşenlerini üretir.
"""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from ... import theme
from .. import icons, surface


def card(parent, *, padx: int = 18, pady: int = 16, accent: str | None = None) -> surface.Panel:
    """Yuvarlatılmış kart. İçerik ``outer.body`` üzerine kurulur.

    ``accent`` geriye dönük uyumluluk için kabul edilir; kart artık şerit yerine
    yalnızca içerik rengiyle ayrışır.
    """
    return surface.Panel(
        parent, radius=18, fill=theme.CARD_BG, border=theme.BORDER,
        pad=max(14, (padx + pady) // 2),
    )


def section(
    parent,
    title: str,
    subtitle: str = "",
    *,
    icon: str | None = None,
    accent: str = theme.PRIMARY,
    action: tk.Widget | None = None,
) -> tk.Frame:
    """Kart içi bölüm başlığı; başlık satırını döner."""
    head = tk.Frame(parent, bg=parent["bg"])
    head.pack(fill="x", pady=(0, 12))
    if icon:
        icons.badge(head, icon, accent, size=34, bg=head["bg"]).pack(
            side="left", padx=(0, 10)
        )
    box = tk.Frame(head, bg=head["bg"])
    box.pack(side="left", fill="x", expand=True)
    tk.Label(
        box,
        text=title,
        font=theme.font(11, True),
        bg=head["bg"],
        fg=theme.TEXT,
        anchor="w",
    ).pack(anchor="w")
    if subtitle:
        tk.Label(
            box,
            text=subtitle,
            font=theme.font(8),
            bg=head["bg"],
            fg=theme.MUTED,
            anchor="w",
        ).pack(anchor="w", pady=(1, 0))
    if action is not None:
        action.pack(in_=head, side="right", padx=(8, 0))
    return head


def metric(
    parent,
    *,
    icon: str,
    title: str,
    value,
    accent: str,
    note: str | None = None,
    spark: list | None = None,
    height: int = 126,
) -> surface.Panel:
    """Büyük dashboard metrik kartı (rozet + başlık + değer, isteğe bağlı sparkline)."""
    outer = surface.Panel(
        parent, radius=18, fill=theme.CARD_BG, border=theme.BORDER, pad=14, height=height,
    )
    body = tk.Frame(outer.body, bg=theme.CARD_BG)
    body.pack(fill="both", expand=True)
    icons.badge(body, icon, accent, size=42, bg=theme.CARD_BG).pack(side="left", anchor="n")
    text = tk.Frame(body, bg=theme.CARD_BG)
    text.pack(side="left", fill="x", expand=True, padx=(12, 4))
    tk.Label(
        text,
        text=title,
        font=theme.font(9),
        bg=theme.CARD_BG,
        fg=theme.MUTED,
        anchor="w",
    ).pack(anchor="w")
    value_label = tk.Label(
        text,
        text=str(value),
        font=theme.display(20),
        bg=theme.CARD_BG,
        fg=theme.TEXT,
        anchor="w",
    )
    value_label.pack(anchor="w", pady=(2, 0))
    outer.value_label = value_label
    if note:
        tk.Label(
            text,
            text=note,
            font=theme.font(8, True),
            bg=theme.CARD_BG,
            fg=accent,
            anchor="w",
        ).pack(anchor="w", pady=(3, 0))
    if spark:
        theme._sparkline(body, spark, accent, width=74, height=34).pack(
            side="right", anchor="s", padx=(2, 0)
        )
    return outer


def table(
    parent,
    columns: tuple[str, ...],
    headings: tuple[str, ...],
    widths: tuple[int, ...],
    *,
    height: int = 12,
    stretch: bool = True,
    show_icon: bool = False,
) -> tuple[ttk.Treeview, tk.Frame]:
    """Modern, koyu tablo; başlık satırı ve dikey kaydırma çubuğuyla.

    ``show_icon=True`` ile ``#0`` sütunu açılır (``tree.item(iid, image=...)``
    üzerinden her satıra örn. bir avatar konabilir).
    """
    wrap = tk.Frame(parent, bg=theme.CARD_BG)
    tree = ttk.Treeview(
        wrap,
        columns=columns,
        show="tree headings" if show_icon else "headings",
        height=height,
        style="Card.Treeview",
        selectmode="browse",
    )
    if show_icon:
        tree.heading("#0", text="")
        tree.column("#0", width=44, minwidth=44, stretch=False, anchor="center")
    for key, text, width in zip(columns, headings, widths, strict=False):
        tree.heading(key, text=text)
        tree.column(
            key,
            width=width,
            minwidth=max(50, width // 2),
            anchor="w",
            stretch=stretch,
        )
    tree.tag_configure("odd", background="#0e1728")
    tree.tag_configure("even", background=theme.CARD_BG)
    tree.pack(side="left", fill="both", expand=True, padx=(0, 1))
    scroll = ttk.Scrollbar(wrap, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=scroll.set)
    scroll.pack(side="right", fill="y")
    return tree, wrap


def badge(parent, text: str, color: str, *, bg: str | None = None) -> tk.Label:
    return tk.Label(
        parent,
        text=text,
        font=theme.font(8, True),
        bg=bg or theme.dark_soft(color, 0.34),
        fg=color,
        padx=8,
        pady=3,
    )


def kv(parent, label: str, value: str, *, width: int = 12) -> tk.Frame:
    row = tk.Frame(parent, bg=parent["bg"])
    tk.Label(
        row,
        text=label,
        font=theme.font(9),
        bg=row["bg"],
        fg=theme.MUTED,
        anchor="w",
        width=width,
    ).pack(side="left")
    tk.Label(
        row,
        text=value or "—",
        font=theme.font(9, True),
        bg=row["bg"],
        fg=theme.TEXT,
        anchor="w",
    ).pack(side="left", fill="x", expand=True)
    return row


def empty(parent, text: str, *, icon: str = "clipboard") -> tk.Frame:
    box = tk.Frame(parent, bg=theme.CARD_BG)
    icons.badge(box, icon, theme.MUTED, size=42, bg=theme.CARD_BG).pack(pady=(18, 8))
    tk.Label(
        box,
        text=text,
        font=theme.font(10),
        bg=theme.CARD_BG,
        fg=theme.MUTED,
    ).pack(pady=(0, 18))
    return box


def field_label(parent, text: str) -> tk.Label:
    return tk.Label(
        parent,
        text=text,
        font=theme.font(8, True),
        bg=parent["bg"],
        fg=theme.MUTED,
        anchor="w",
    )


def notice(parent, text: str, *, accent: str = theme.PRIMARY, icon: str = "alert",
           wraplength: int = 760) -> surface.Panel:
    row = surface.Panel(
        parent, radius=12, fill=theme.dark_soft(accent, 0.18),
        border=theme.mix(accent, theme.CARD_BG, 0.45), pad=10,
    )
    box = row.body
    icons.icon(box, icon, size=16, color=accent, bg=box["bg"]).pack(side="left", padx=(2, 10))
    tk.Label(
        box,
        text=text,
        font=theme.font(9),
        bg=box["bg"],
        fg=theme.TEXT,
        anchor="w",
        justify="left",
        wraplength=wraplength,
    ).pack(side="left", fill="x", expand=True)
    return row


def segmented(
    parent,
    options: tuple[tuple[str, str], ...],
    *,
    active: str,
    command,
) -> tuple[tk.Frame, dict[str, tk.Label]]:
    """Alt sekme düğmeleri; ``options`` = ((anahtar, etiket), ...)."""
    bar = tk.Frame(parent, bg=theme.CARD_2)
    labels: dict[str, tk.Label] = {}

    def select(key: str) -> None:
        for k, lbl in labels.items():
            on = k == key
            lbl.configure(
                bg=theme.PRIMARY if on else theme.CARD_2,
                fg="white" if on else theme.MUTED,
            )
        command(key)

    for key, text in options:
        lbl = tk.Label(
            bar,
            text=text,
            font=theme.font(9, True),
            bg=theme.PRIMARY if key == active else theme.CARD_2,
            fg="white" if key == active else theme.MUTED,
            padx=14,
            pady=6,
            cursor="hand2",
        )
        lbl.pack(side="left", padx=(0, 2), pady=2)
        lbl.bind("<Button-1>", lambda _e, k=key: select(k))
        labels[key] = lbl
    return bar, labels


class Page(tk.Frame):
    """Tüm iç sayfalar için ortak iskelet."""

    title = "Sayfa"
    subtitle = ""
    icon = "home"
    accent = theme.PRIMARY

    def __init__(self, parent, app) -> None:
        super().__init__(parent, bg=theme.APP_BG)
        self.app = app
        self.body = tk.Frame(self, bg=theme.APP_BG)
        self.body.pack(fill="both", expand=True, padx=22, pady=(16, 22))
        self.build()

    def build(self) -> None:  # pragma: no cover - alt sınıflar doldurur
        raise NotImplementedError

    def page_head(
        self,
        title: str | None = None,
        subtitle: str | None = None,
        *,
        actions: tuple[tk.Widget, ...] = (),
        avatar: tuple[str, str] | None = None,
    ) -> tk.Frame:
        """``avatar`` verilirse (baş harfler, renk) jenerik ikon yerine kişi avatarı basılır."""
        head = tk.Frame(self.body, bg=theme.APP_BG)
        head.pack(fill="x", pady=(0, 14))
        if avatar is not None:
            initials, color = avatar
            surface.Avatar(head, initials, color, size=46, bg=theme.APP_BG).pack(
                side="left", padx=(0, 12)
            )
        else:
            icons.badge(head, self.icon, self.accent, size=46, bg=theme.APP_BG).pack(
                side="left", padx=(0, 12)
            )
        text = tk.Frame(head, bg=theme.APP_BG)
        text.pack(side="left", fill="x", expand=True)
        tk.Label(
            text,
            text=title or self.title,
            font=theme.font(21, True),
            bg=theme.APP_BG,
            fg=theme.TEXT,
            anchor="w",
        ).pack(anchor="w")
        if subtitle or self.subtitle:
            tk.Label(
                text,
                text=subtitle if subtitle is not None else self.subtitle,
                font=theme.font(9),
                bg=theme.APP_BG,
                fg=theme.MUTED,
                anchor="w",
            ).pack(anchor="w", pady=(2, 0))
        row = tk.Frame(head, bg=theme.APP_BG)
        row.pack(side="right", padx=(10, 0))
        for action in actions:
            action.pack(in_=row, side="left", padx=(6, 0))
        return head

    def refresh(self) -> None:
        """Sayfayı yeniden kur (router tarafından çağrılır)."""


def stat_grid(parent, cards: list[tk.Frame], *, columns: int = 4) -> None:
    for idx, card_widget in enumerate(cards):
        row, col = divmod(idx, columns)
        card_widget.grid(row=row, column=col, sticky="nsew", padx=5, pady=5)
    for col in range(columns):
        parent.grid_columnconfigure(col, weight=1, uniform="metric")
