"""Hasta — randevularım (v2'de eklenen yeni özellik)."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from ... import state, theme
from ...db import patients as patients_db
from .. import helpers


def show_appointments_screen() -> None:
    win = helpers.modal_window(None, "Randevularım", "780x520")
    helpers.header(
        win,
        "🗓️ Randevularım",
        "Doktorunuz tarafından oluşturulan muayene/kontrol randevuları",
    )

    card = theme.frame(win, card=True)
    card.pack(fill="both", expand=True, padx=16, pady=(0, 12))
    tree = ttk.Treeview(
        card,
        columns=("tarih", "saat", "sure", "doktor", "uzmanlik", "durum", "not"),
        show="headings",
        height=12,
        style="Card.Treeview",
    )
    for key, text, width in (
        ("tarih", "Tarih", 100),
        ("saat", "Saat", 70),
        ("sure", "Süre", 60),
        ("doktor", "Doktor", 180),
        ("uzmanlik", "Uzmanlık", 120),
        ("durum", "Durum", 100),
        ("not", "Not", 180),
    ):
        tree.heading(key, text=text)
        tree.column(key, width=width, anchor="w")
    tree.pack(side="left", fill="both", expand=True, padx=(1, 0), pady=1)
    vsb = ttk.Scrollbar(card, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=vsb.set)
    vsb.pack(side="right", fill="y")

    tree.tag_configure("success", background="#e9f4ea")
    tree.tag_configure("canceled", background=theme.READ_BG, foreground=theme.MUTED)

    empty_label: ttk.Label | tk.Label | None = None

    def refresh() -> None:
        nonlocal empty_label
        rows = patients_db.appointments_for_patient(state.session.patient_id)
        tree.delete(*tree.get_children())
        for row in rows:
            done = row["durum"] == "Tamamlandı"
            tree.insert(
                "",
                "end",
                tags=("success" if done else "canceled",),
                values=(
                    helpers.date_label(row["randevu_tarihi"]),
                    row["randevu_saati"],
                    f"{row['sure_dakika']} dk",
                    row["doktor_adi"],
                    row["uzmanlik"] or "—",
                    row["durum"],
                    row["not_metni"] or "—",
                ),
            )
        if empty_label is not None:
            empty_label.destroy()
            empty_label = None
        if not rows:
            empty_label = theme.muted_label(card, "Henüz randevunuz yok.", 10)
            empty_label.pack(pady=8)

    bar = theme.frame(win)
    bar.pack(fill="x", padx=16, pady=(0, 12))
    theme.button(bar, "Yenile", refresh, style="primary").pack(side="right")
    refresh()
