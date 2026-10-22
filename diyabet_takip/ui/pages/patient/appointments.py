"""Hasta — randevularım."""

from __future__ import annotations

import tkinter as tk
from tkinter import messagebox

from .... import state, theme
from ....db import doctors as doctors_db
from ....db import patients as patients_db
from ..base import Page, card, empty, metric, section, stat_grid, table


class PatientAppointmentsPage(Page):
    title = "Randevularım"
    subtitle = "Doktorunuzun oluşturduğu muayene ve kontrol randevularını görün."
    icon = "calendar"
    accent = theme.AMBER

    def build(self) -> None:
        self.page_head()
        rows = patients_db.appointments_for_patient(state.session.patient_id)
        self.rows = rows
        upcoming = [r for r in rows if r["durum"] == "Planlandı"]
        done = [r for r in rows if r["durum"] == "Tamamlandı"]
        canceled = [r for r in rows if r["durum"] == "İptal Edildi"]
        stats = tk.Frame(self.body, bg=theme.APP_BG)
        stats.pack(fill="x", pady=(0, 12))
        cards = [
            metric(stats, icon="calendar", title="Planlanan", value=len(upcoming), accent=theme.AMBER),
            metric(stats, icon="check", title="Tamamlanan", value=len(done), accent=theme.GREEN),
            metric(stats, icon="alert", title="İptal", value=len(canceled), accent=theme.BLOOD),
            metric(stats, icon="clock", title="Toplam", value=len(rows), accent=theme.CYAN),
        ]
        stat_grid(stats, cards, columns=4)
        outer = card(self.body, padx=0, pady=0)
        outer.pack(fill="both", expand=True)
        head = tk.Frame(outer.body, bg=theme.CARD_BG)
        head.pack(fill="x", padx=14, pady=(12, 8))
        section_head = section(
            head, "Randevu Listesi", "Tarih ve saat bilgileri",
            icon="calendar", accent=theme.AMBER,
        )
        cancel_btn = theme.button(section_head, "Seçileni İptal Et", self._cancel, style="danger")
        cancel_btn.pack(side="right", padx=(8, 0))
        tree, wrap = table(
            outer.body,
            ("tarih", "saat", "sure", "doktor", "uzmanlik", "durum", "not"),
            ("Tarih", "Saat", "Süre", "Doktor", "Uzmanlık", "Durum", "Not"),
            (105, 75, 70, 200, 150, 120, 260), height=14,
        )
        wrap.pack(fill="both", expand=True, padx=10, pady=(0, 12))
        tree.tag_configure("Planlandı", background=theme.WARNING_BG)
        tree.tag_configure("Tamamlandı", background="#12301f")
        tree.tag_configure("İptal Edildi", background=theme.READ_BG)
        for row in rows:
            tree.insert("", "end", iid=str(row["randevu_id"]), tags=(row["durum"],), values=(
                row["randevu_tarihi"].strftime("%d.%m.%Y"), row["randevu_saati"],
                f"{row['sure_dakika']} dk", row["doktor_adi"], row["uzmanlik"] or "—",
                row["durum"], row["not_metni"] or "—",
            ))
        self.tree = tree
        if not rows:
            empty(outer.body, "Henüz randevunuz yok.", icon="calendar").pack(fill="both", expand=True)

    def _cancel(self) -> None:
        selection = self.tree.selection()
        if not selection:
            messagebox.showinfo("Randevu", "İptal etmek için listeden bir randevu seçin.", parent=self)
            return
        row = next((r for r in self.rows if str(r["randevu_id"]) == selection[0]), None)
        if row is None:
            return
        if row["durum"] != "Planlandı":
            messagebox.showinfo("Randevu", "Yalnızca planlanan randevular iptal edilebilir.", parent=self)
            return
        if not messagebox.askyesno(
            "Randevuyu İptal Et",
            f"{row['randevu_tarihi'].strftime('%d.%m.%Y')} {row['randevu_saati']} randevunuz iptal edilsin mi?",
            parent=self,
        ):
            return
        if doctors_db.cancel_appointment(row["randevu_id"]):
            self.app.navigate("patient_appointments")
        else:
            messagebox.showerror("Randevu", "Randevu iptal edilemedi.", parent=self)

    def refresh(self) -> None:
        self.app.navigate("patient_appointments")
