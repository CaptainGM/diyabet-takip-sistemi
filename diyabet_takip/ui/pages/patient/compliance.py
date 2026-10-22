"""Hasta — diyet/egzersiz/ölçüm uyum takibi."""

from __future__ import annotations

import tkinter as tk

from .... import state, theme
from ....db import records as records_db
from ... import charts
from ..base import Page, card, empty, metric, notice, section, stat_grid, table


class CompliancePage(Page):
    title = "Uyum Takibi"
    subtitle = "Diyet, egzersiz ve ölçüm alışkanlıklarınızın son 30 günlük görünümü."
    icon = "target"
    accent = theme.GREEN

    def build(self) -> None:
        self.page_head(
            actions=(
                theme.button(self, "Diyet / Egzersiz Kaydet", lambda: self.app.navigate("lifestyle"), style="primary"),
            )
        )
        history = records_db.compliance_history(state.session.patient_id, limit=30)
        latest = history[0] if history else None
        stats = tk.Frame(self.body, bg=theme.APP_BG)
        stats.pack(fill="x", pady=(0, 12))
        cards = [
            metric(stats, icon="target", title="Genel Skor", value=f"%{latest['genel_uyum_skoru']:.0f}" if latest else "—",
                   accent=theme.GREEN, note="Son hesaplama"),
            metric(stats, icon="apple", title="Diyet Uyumu", value=f"%{latest['diyet_uyum_orani']:.0f}" if latest else "—",
                   accent=theme.GREEN, note="Son 7 gün"),
            metric(stats, icon="dumbbell", title="Egzersiz Uyumu", value=f"%{latest['egzersiz_uyum_orani']:.0f}" if latest else "—",
                   accent=theme.ORANGE, note="Son 7 gün"),
            metric(stats, icon="droplet", title="Ölçüm Uyumu", value=f"%{latest['olcum_uyum_orani']:.0f}" if latest else "—",
                   accent=theme.BLOOD, note="Son 7 gün"),
        ]
        stat_grid(stats, cards, columns=4)

        chart = card(self.body, padx=10, pady=10, accent=theme.GREEN)
        chart.pack(fill="x", pady=(0, 12))
        section(chart.body, "Uyum Eğilimi", "Son 30 günün yüzdelik değişimi", icon="chart", accent=theme.GREEN)
        try:
            charts.plot_compliance_percentages(chart.body, history, role_for_title="Hasta")
        except Exception:
            notice(chart.body, "Grafik çizilemedi.", accent=theme.BLOOD).pack(fill="x")

        outer = card(self.body, padx=0, pady=0)
        outer.pack(fill="both", expand=True)
        head = tk.Frame(outer.body, bg=theme.CARD_BG)
        head.pack(fill="x", padx=14, pady=(12, 8))
        section(head, "Uyum Geçmişi", "Hesaplama tarihine göre skorlar", icon="clipboard", accent=theme.GREEN)
        tree, wrap = table(
            outer.body,
            ("tarih", "diyet", "egz", "olcum", "genel"),
            ("Hesap Tarihi", "Diyet", "Egzersiz", "Ölçüm", "Genel Skor"),
            (130, 150, 150, 150, 150), height=10,
        )
        wrap.pack(fill="both", expand=True, padx=10, pady=(0, 12))
        for idx, row in enumerate(history):
            tree.insert("", "end", tags=("odd" if idx % 2 else "even",), values=(
                row["hesaplama_tarihi"].strftime("%d.%m.%Y"),
                f"%{row['diyet_uyum_orani']:.0f}", f"%{row['egzersiz_uyum_orani']:.0f}",
                f"%{row['olcum_uyum_orani']:.0f}", f"%{row['genel_uyum_skoru']:.0f}",
            ))
        if not history:
            empty(outer.body, "Henüz uyum kaydı yok. Diyet / egzersiz kaydı ekleyin.", icon="target").pack(
                fill="both", expand=True
            )

    def refresh(self) -> None:
        self.app.navigate("compliance")
