"""Hasta — ölçüm geçmişi ve trend grafiği."""

from __future__ import annotations

import tkinter as tk

from .... import state, theme
from ....db import records as records_db
from ....db import reference as ref
from ....db.client import get_db
from ... import charts
from ..base import Page, card, empty, metric, notice, section, stat_grid, table
from ._common import MEAL_TIPS_ALL, _num


class HistoryPage(Page):
    title = "Geçmiş & Grafik"
    subtitle = "Kan şekeri değişiminizi inceleyin, hedef aralığınızı ve ölçüm geçmişinizi görün."
    icon = "chart"
    accent = theme.CYAN

    def build(self) -> None:
        self.page_head(
            actions=(
                theme.button(self, "Ölçüm Gir", lambda: self.app.navigate("measure"), style="primary"),
            )
        )
        self.series = records_db.measurement_series(state.session.patient_id, limit=200)
        self.rows = records_db.recent_measurements(state.session.patient_id, limit=200)
        self._build_metrics()
        chart_card = card(self.body, padx=10, pady=10, accent=theme.CYAN)
        chart_card.pack(fill="x", pady=(0, 12))
        section(chart_card.body, "Kan Şekeri Trendi", "Son ölçümler · hedef aralık vurgulu",
                icon="trend", accent=theme.CYAN)
        self.chart_host = tk.Frame(chart_card.body, bg=theme.CARD_BG)
        self.chart_host.pack(fill="x")
        db = get_db()
        profile = ref.find_patient_profile(db, state.session.patient_id) or {} if db is not None else {}
        self.target = (profile.get("hedef_kan_sekeri_min", 70), profile.get("hedef_kan_sekeri_max", 140))
        try:
            charts.plot_blood_sugar_trend(self.chart_host, self.series, target_range=self.target)
        except Exception:
            notice(self.chart_host, "Grafik çizilemedi.", accent=theme.BLOOD).pack(fill="x")
        self._build_table()

    def _build_metrics(self) -> None:
        values = [m["kan_sekeri_degeri"] for m in self.series]
        box = tk.Frame(self.body, bg=theme.APP_BG)
        box.pack(fill="x", pady=(0, 12))
        cards = [
            metric(box, icon="droplet", title="Son Ölçüm", value=_num(values[-1] if values else None),
                   accent=theme.BLOOD, note="En yeni kayıt"),
            metric(box, icon="chart", title="Ortalama", value=_num(sum(values) / len(values) if values else None),
                   accent=theme.PRIMARY, note="Tüm kayıtlar"),
            metric(box, icon="trend", title="En Düşük", value=_num(min(values) if values else None),
                   accent=theme.AMBER, note="Tüm kayıtlar"),
            metric(box, icon="trend", title="En Yüksek", value=_num(max(values) if values else None),
                   accent=theme.BLOOD, note="Tüm kayıtlar"),
        ]
        stat_grid(box, cards, columns=4)

    def _build_table(self) -> None:
        outer = card(self.body, padx=0, pady=0)
        outer.pack(fill="both", expand=True)
        head = tk.Frame(outer.body, bg=theme.CARD_BG)
        head.pack(fill="x", padx=14, pady=(12, 8))
        section(head, "Ölçüm Geçmişi", "Tüm geçerli ve geçersiz ölçümler", icon="clipboard", accent=theme.CYAN)
        filter_row = tk.Frame(head, bg=theme.CARD_BG)
        filter_row.pack(side="right", pady=(4, 0))
        self.filter_var = tk.StringVar(value="Tümü")
        menu = tk.OptionMenu(filter_row, self.filter_var, *MEAL_TIPS_ALL, command=lambda _v: self._fill())
        menu.configure(font=theme.font(9), bg=theme.DARK_FIELD, fg=theme.TEXT,
                       activebackground=theme.PRIMARY_DARK, relief="flat",
                       highlightthickness=1, highlightbackground=theme.BORDER, width=10)
        menu["menu"].configure(bg=theme.CARD_BG, fg=theme.TEXT, activebackground=theme.PRIMARY_DARK)
        menu.pack(side="right")
        self.tree, wrap = table(
            outer.body,
            ("tarih", "saat", "tip", "deger", "gecerli", "not"),
            ("Tarih", "Saat", "Öğün", "Kan Şekeri", "Ortalamaya Dahil", "Not"),
            (105, 75, 100, 135, 150, 360), height=12,
        )
        wrap.pack(fill="both", expand=True, padx=10, pady=(0, 12))
        self.tree.tag_configure("low", background=theme.WARNING_BG)
        self.tree.tag_configure("high", background=theme.CRITICAL_BG)
        self._fill()

    def _fill(self) -> None:
        if getattr(self, "empty_state", None) is not None:
            self.empty_state.destroy()
            self.empty_state = None
        tip = self.filter_var.get()
        self.tree.delete(*self.tree.get_children())
        rows = [m for m in self.rows if tip == "Tümü" or m["olcum_tipi"] == tip]
        for idx, m in enumerate(rows):
            value = m["kan_sekeri_degeri"]
            tag = "low" if value < 70 else "high" if value > 200 else "odd" if idx % 2 else "even"
            self.tree.insert("", "end", tags=(tag,), values=(
                m["olcum_tarihi"].strftime("%d.%m.%Y"),
                m["olcum_saati"].strftime("%H:%M") if m["olcum_saati"] else "—",
                m["olcum_tipi"], f"{value:g} mg/dL",
                "Evet" if m["gecerli_olcum"] else "Hayır", m["notlar"] or "—",
            ))
        if not rows:
            self.empty_state = empty(self.tree.master, "Bu filtreye uygun ölçüm yok.", icon="droplet")
            self.empty_state.pack(fill="both", expand=True)

    def refresh(self) -> None:
        self.app.navigate("history")
