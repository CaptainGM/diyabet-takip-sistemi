"""Hasta — insülin önerileri."""

from __future__ import annotations

import datetime
import tkinter as tk
from tkinter import messagebox

from .... import state, theme
from ....db import patients as patients_db
from ....db import records as records_db
from ..base import Page, card, empty, field_label, metric, section, stat_grid, table
from ._common import MEAL_TIPS_ALL


class InsulinPage(Page):
    title = "İnsülin"
    subtitle = "Öğün ortalamalarına göre hazırlanan insülin önerilerinizi takip edin."
    icon = "syringe"
    accent = theme.PURPLE

    def build(self) -> None:
        self.recs: dict[str, dict] = {}
        self.page_head(actions=(theme.button(self, "Yenile", self.refresh, style="ghost"),))
        stats = tk.Frame(self.body, bg=theme.APP_BG)
        stats.pack(fill="x", pady=(0, 12))
        cards = [
            metric(stats, icon="syringe", title="Öneri", value="—", accent=theme.PURPLE, note="Seçili aralık"),
            metric(stats, icon="check", title="Uygulanan", value="—", accent=theme.GREEN, note="İşaretlenen doz"),
            metric(stats, icon="clock", title="Bekleyen", value="—", accent=theme.AMBER, note="Uygulanmayı bekliyor"),
            metric(stats, icon="chart", title="Ortalama Doz", value="—", accent=theme.CYAN, note="ml"),
        ]
        stat_grid(stats, cards, columns=4)
        self.metric_cards = cards

        filters = card(self.body, padx=14, pady=12)
        filters.pack(fill="x", pady=(0, 12))
        row = tk.Frame(filters.body, bg=theme.CARD_BG)
        row.pack(fill="x")
        field_label(row, "Öğün").pack(side="left", padx=(0, 4))
        self.tip = tk.StringVar(value="Tümü")
        menu = tk.OptionMenu(row, self.tip, *MEAL_TIPS_ALL)
        menu.configure(font=theme.font(9), bg=theme.DARK_FIELD, fg=theme.TEXT,
                       activebackground=theme.PRIMARY_DARK, relief="flat",
                       highlightthickness=1, highlightbackground=theme.BORDER, width=10)
        menu["menu"].configure(bg=theme.CARD_BG, fg=theme.TEXT, activebackground=theme.PRIMARY_DARK)
        menu.pack(side="left", padx=(0, 14))
        field_label(row, "Başlangıç").pack(side="left", padx=(0, 4))
        self.start = theme.date_entry(row)
        self.start.set_date(datetime.date.today() - datetime.timedelta(days=30))
        self.start.pack(side="left", padx=(0, 14))
        field_label(row, "Bitiş").pack(side="left", padx=(0, 4))
        self.end = theme.date_entry(row)
        self.end.pack(side="left", padx=(0, 14))
        theme.button(row, "Filtrele", self._load, style="primary").pack(side="left")
        theme.button(row, "Seçileni Uygulandı İşaretle", self._mark, style="success").pack(side="right")

        outer = card(self.body, padx=0, pady=0)
        outer.pack(fill="both", expand=True)
        head = tk.Frame(outer.body, bg=theme.CARD_BG)
        head.pack(fill="x", padx=14, pady=(12, 8))
        section(head, "İnsülin Önerileri", "Doz uygulandıysa satırı seçip işaretleyin.", icon="syringe", accent=theme.PURPLE)
        self.tree, wrap = table(
            outer.body,
            ("tarih", "tip", "ortalama", "doz", "durum"),
            ("Tarih", "Öğün", "Ortalama Kan Şekeri", "Önerilen Doz", "Durum"),
            (120, 120, 190, 160, 150), height=12,
        )
        wrap.pack(fill="both", expand=True, padx=10, pady=(0, 12))
        self.tree.tag_configure("pending", background=theme.WARNING_BG)
        self.tree.tag_configure("done", background=theme.READ_BG)
        self.empty_label = None
        self._load()

    def _load(self) -> None:
        start, end = self.start.get_date(), self.end.get_date()
        if end < start:
            messagebox.showerror("Tarih", "Bitiş tarihi başlangıçtan önce olamaz.", parent=self)
            return
        rows = records_db.insulin_history(state.session.patient_id, start=start, end=end, limit=200)
        if self.tip.get() != "Tümü":
            rows = [r for r in rows if r["olcum_tipi"] == self.tip.get()]
        self.recs = {str(r["oneri_id"]): r for r in rows}
        self.tree.delete(*self.tree.get_children())
        if self.empty_label is not None:
            self.empty_label.destroy()
            self.empty_label = None
        for row in rows:
            self.tree.insert("", "end", iid=str(row["oneri_id"]),
                             tags=("done",) if row["uygulandi"] else ("pending",),
                             values=(
                                 row["tarih"].strftime("%d.%m.%Y"), row["olcum_tipi"],
                                 f"{row['ortalama_kan_sekeri']:g} mg/dL",
                                 f"{row['onerilen_doz_ml']:g} ml",
                                 "Uygulandı" if row["uygulandi"] else "Bekliyor",
                             ))
        if not rows:
            self.empty_label = empty(self.tree.master, "Bu aralıkta öneri yok.", icon="syringe")
            self.empty_label.pack(fill="both", expand=True)
        applied = sum(1 for r in rows if r["uygulandi"])
        doses = [r["onerilen_doz_ml"] for r in rows]
        values = [
            str(len(rows)), str(applied), str(len(rows) - applied),
            f"{sum(doses) / len(doses):.1f}" if doses else "—",
        ]
        for card_widget, value in zip(self.metric_cards, values, strict=False):
            card_widget.value_label.configure(text=value)

    def _mark(self) -> None:
        selection = self.tree.focus()
        if not selection:
            messagebox.showinfo("İnsülin", "Önce bir öneri seçin.", parent=self)
            return
        ok = patients_db.mark_insulin_applied(self.recs[selection]["oneri_id"], state.session.patient_id)
        if ok:
            self._load()
        else:
            messagebox.showerror("İnsülin", "İşaretlenemedi.", parent=self)

    def refresh(self) -> None:
        self._load()
