"""Doktor — randevu oluşturma, iptal ve takvim."""

from __future__ import annotations

import datetime
import tkinter as tk
from tkinter import messagebox

from .... import state, theme
from ....db import doctors as doctors_db
from ..base import Page, card, empty, field_label, metric, notice, section, stat_grid, table
from ._common import _date


class AppointmentsPage(Page):
    title = "Randevular"
    subtitle = "Muayene takvimini planlayın ve randevu durumlarını izleyin."
    icon = "calendar"
    accent = theme.AMBER

    def build(self) -> None:
        self.rows = []
        self.page_head(actions=(theme.button(self, "Yenile", self._load, style="ghost"),))
        rows = doctors_db.appointments_for_doctor(state.session.doctor_id)
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

        body = tk.Frame(self.body, bg=theme.APP_BG)
        body.pack(fill="both", expand=True)
        left = card(body, padx=16, pady=14, accent=theme.AMBER)
        left.pack(side="left", fill="both", padx=(0, 6))
        left.configure(width=360)
        left.pack_propagate(False)
        section(left.body, "Yeni Randevu", "Hasta, tarih ve saat bilgilerini girin.",
                icon="calendar", accent=theme.AMBER)
        form = tk.Frame(left.body, bg=theme.CARD_BG)
        form.pack(fill="x")
        patients = doctors_db.list_patients_for_doctor(state.session.doctor_id)
        self.patient_map = {f"{p['ad']} {p['soyad']} · {p['tc_kimlik_no']}": p for p in patients}
        self.patient_var = tk.StringVar(value=next(iter(self.patient_map), "Hasta yok"))
        menu = tk.OptionMenu(form, self.patient_var, *(self.patient_map.keys() or ["Hasta yok"]))
        menu.configure(font=theme.font(9), bg=theme.DARK_FIELD, fg=theme.TEXT,
                       activebackground=theme.PRIMARY_DARK, relief="flat",
                       highlightthickness=1, highlightbackground=theme.BORDER)
        menu["menu"].configure(bg=theme.CARD_BG, fg=theme.TEXT, activebackground=theme.PRIMARY_DARK)
        field_label(form, "Hasta").pack(anchor="w", pady=(4, 0))
        menu.pack(fill="x", pady=(3, 8))
        field_label(form, "Tarih").pack(anchor="w")
        self.date = theme.date_entry(form)
        self.date.pack(fill="x", pady=(3, 8))
        field_label(form, "Saat (SS:DD)").pack(anchor="w")
        self.time = theme.entry(form, width=12)
        self.time.insert(0, datetime.datetime.now().strftime("%H:%M"))
        self.time.pack(fill="x", pady=(3, 8))
        field_label(form, "Süre (dk)").pack(anchor="w")
        self.duration = theme.spinbox(form, from_=10, to=180, width=10, increment=5)
        self.duration.delete(0, tk.END)
        self.duration.insert(0, 30)
        self.duration.pack(fill="x", pady=(3, 8))
        field_label(form, "Not").pack(anchor="w")
        self.note = theme.entry(form, width=30)
        self.note.pack(fill="x", pady=(3, 10))
        theme.button(left.body, "Randevu Oluştur", self._create, style="primary").pack(fill="x")
        notice(left.body, "Aynı tarih ve saatte ikinci bir planlı randevu oluşturulamaz.",
               accent=theme.AMBER, icon="clock", wraplength=300).pack(fill="x", pady=(10, 0))

        right = card(body, padx=0, pady=0)
        right.pack(side="left", fill="both", expand=True, padx=(6, 0))
        head = tk.Frame(right.body, bg=theme.CARD_BG)
        head.pack(fill="x", padx=14, pady=(12, 8))
        section_head = section(
            head, "Randevu Takvimi", "Planlanan randevular ve geçmiş kayıtlar",
            icon="calendar", accent=theme.AMBER,
        )
        cancel_btn = theme.button(section_head, "Seçileni İptal Et", self._cancel, style="danger")
        cancel_btn.pack(side="right", padx=(8, 0))
        self.tree, wrap = table(
            right.body,
            ("hasta", "tarih", "saat", "sure", "durum", "not"),
            ("Hasta", "Tarih", "Saat", "Süre", "Durum", "Not"),
            (220, 105, 75, 75, 130, 240), height=15,
        )
        wrap.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        self.tree.tag_configure("Planlandı", background=theme.WARNING_BG)
        self.tree.tag_configure("Tamamlandı", background="#12301f")
        self.tree.tag_configure("İptal Edildi", background=theme.READ_BG)
        self._load()

    def _load(self) -> None:
        rows = doctors_db.appointments_for_doctor(state.session.doctor_id)
        self.rows = rows
        self.tree.delete(*self.tree.get_children())
        for row in rows:
            self.tree.insert("", "end", iid=str(row["randevu_id"]), tags=(row["durum"],), values=(
                f"{row['hasta_adi']} ({row['hasta_tc']})", _date(row["randevu_tarihi"]),
                row["randevu_saati"], f"{row['sure_dakika']} dk", row["durum"], row["not_metni"] or "—",
            ))
        if not rows:
            empty(self.tree.master, "Henüz randevu yok.", icon="calendar").pack(fill="both", expand=True)

    def _create(self) -> None:
        patient = self.patient_map.get(self.patient_var.get())
        if not patient:
            messagebox.showinfo("Randevu", "Önce bir hasta seçin.", parent=self)
            return
        try:
            datetime.datetime.strptime(self.time.get().strip(), "%H:%M")
        except ValueError:
            messagebox.showerror("Randevu", "Saat SS:DD biçiminde olmalıdır (örn. 14:30).", parent=self)
            return
        day = self.date.get_date()
        clock = self.time.get().strip()
        for row in self.rows:
            if row["durum"] == "Planlandı" and row["randevu_tarihi"] == day and row["randevu_saati"] == clock:
                messagebox.showwarning("Randevu", "Bu tarih ve saatte zaten planlı bir randevu var.", parent=self)
                return
        result = doctors_db.create_appointment(
            state.session.doctor_id, patient["tc_kimlik_no"], day, clock,
            int(self.duration.get()), self.note.get().strip(),
        )
        if result["ok"]:
            self.note.delete(0, tk.END)
            self._load()
            messagebox.showinfo("Randevu", result["mesaj"], parent=self)
        else:
            messagebox.showerror("Randevu", result["mesaj"], parent=self)

    def refresh(self) -> None:
        self._load()

    def _cancel(self) -> None:
        selection = self.tree.selection()
        if not selection:
            messagebox.showinfo("Randevu", "İptal etmek için listeden bir randevu seçin.", parent=self)
            return
        appointment_id = selection[0]
        row = next((r for r in self.rows if str(r["randevu_id"]) == appointment_id), None)
        if row is None:
            return
        if row["durum"] != "Planlandı":
            messagebox.showinfo("Randevu", "Yalnızca planlanan randevular iptal edilebilir.", parent=self)
            return
        if not messagebox.askyesno(
            "Randevuyu İptal Et",
            f"{row['hasta_adi']} için {_date(row['randevu_tarihi'])} {row['randevu_saati']} randevusu iptal edilsin mi?",
            parent=self,
        ):
            return
        if doctors_db.cancel_appointment(row["randevu_id"]):
            self._load()
            messagebox.showinfo("Randevu", "Randevu iptal edildi.", parent=self)
        else:
            messagebox.showerror("Randevu", "Randevu iptal edilemedi.", parent=self)
