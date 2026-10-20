"""Doktor dashboard'u — v1'de sadece veritabanı görünümüydü; v2'de ekran."""
from __future__ import annotations

import tkinter as tk

from ... import state, theme
from ...db import doctors as doctors_db
from .. import helpers


def show_doctor_dashboard() -> None:
    win = helpers.modal_window(None, "Doktor Paneli", "980x420")
    helpers.header(win, "📊 Panelim — Durum Özeti", f"{state.session.full_name} için günlük özet")

    try:
        stats = doctors_db.doctor_dashboard(state.session.doctor_id)
        alerts = doctors_db.patient_alerts_for_doctor(state.session.doctor_id, limit=6)
    except Exception as exc:  # bağlantı vb.
        helpers.info_panel(win, f"Panel verisi yüklenemedi: {exc}", "⚠️")
        return

    container = theme.frame(win)
    container.pack(fill="both", expand=True, padx=20, pady=10)
    for col in range(2):
        container.grid_columnconfigure(col, weight=1)

    cards = [
        ("👥", "Toplam Hasta", stats.get("toplam_hasta_sayisi", 0)),
        ("🩸", "Bugün Ölçüm Yapan Hasta", stats.get("bugun_olcum_yapan_hasta_sayisi", 0)),
        ("🚨", "Okunmamış Uyarı", stats.get("okunmamis_uyari_sayisi", 0)),
        ("📅", "Bugün Gelen Uyarı", stats.get("bugun_uyari_sayisi", 0)),
        ("🎯", "7 Günlük Ortalama Uyum Skoru", f"%{stats.get('ortalama_hasta_uyum_skoru', 0)}"),
    ]
    for index, (icon, title, value) in enumerate(cards):
        cell = theme.frame(container, card=True)
        row, col = divmod(index, 2)
        cell.grid(row=row, column=col, padx=12, pady=10, sticky="nsew")
        tk.Label(cell, text=icon, font=("Segoe UI Emoji", 22), bg=theme.CARD_BG).pack(pady=(16, 2))
        tk.Label(
            cell, text=title, font=theme.font(10), bg=theme.CARD_BG, fg=theme.MUTED
        ).pack()
        tk.Label(
            cell, text=str(value), font=theme.font(20, True), bg=theme.CARD_BG, fg=theme.PRIMARY
        ).pack(pady=(0, 18))

    recent = theme.frame(win, card=True)
    recent.pack(fill="both", expand=True, padx=20, pady=(0, 20))
    theme.label(recent, "Son Uyarılar", 11, bold=True).pack(anchor="w", padx=14, pady=(10, 4))
    if alerts:
        for alert in alerts:
            badge = "🔴" if alert["aciliyet_seviyesi"] == "Kritik" else "🟠" if alert["aciliyet_seviyesi"] == "Yüksek" else "🟡"
            theme.label(
                recent,
                f"{badge} {alert['hasta_adi']} — {alert['uyari_adi']}"
                f"{' (okunmadı)' if not alert['okundu'] else ''}",
                9,
            ).pack(anchor="w", padx=14, pady=2)
    else:
        theme.muted_label(recent, "Son 6 uyarı yok — güzel haber!", 9).pack(anchor="w", padx=14, pady=(0, 10))
