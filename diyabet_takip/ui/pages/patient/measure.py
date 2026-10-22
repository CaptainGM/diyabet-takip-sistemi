"""Hasta — kan şekeri ölçümü girişi."""

from __future__ import annotations

import datetime
import tkinter as tk
from tkinter import messagebox

from .... import state, theme
from ....db import records as records_db
from ....db import reference as ref
from ....db.client import get_db
from ....services import measurement_service
from ..base import Page, card, field_label, metric, notice, section, stat_grid
from ._common import MEAL_TIPS, _num


class MeasurePage(Page):
    title = "Ölçüm Gir"
    subtitle = "Kan şekeri ölçümünüzü kaydedin; uygun saat aralığında otomatik olarak ortalamalara eklenir."
    icon = "droplet"
    accent = theme.BLOOD

    def build(self) -> None:
        self.page_head(
            actions=(
                theme.button(self, "Geçmiş", lambda: self.app.navigate("history"), style="ghost"),
                theme.button(self, "Uyum Takibi", lambda: self.app.navigate("compliance"), style="ghost"),
            )
        )
        self._build_metrics()
        body = tk.Frame(self.body, bg=theme.APP_BG)
        body.pack(fill="both", expand=True)

        left = card(body, padx=18, pady=16, accent=theme.BLOOD)
        left.pack(side="left", fill="both", expand=True, padx=(0, 7))
        section(left.body, "Yeni Ölçüm", "Değer ve öğün bilgisini girin.", icon="droplet", accent=theme.BLOOD)
        form = tk.Frame(left.body, bg=theme.CARD_BG)
        form.pack(fill="x")
        field_label(form, "Kan şekeri değeri").pack(anchor="w")
        value_box = theme.entry_with_unit(form, "mg/dL", accent=theme.BLOOD, width=22)
        value_box.pack(fill="x", pady=(4, 12))
        self.value = value_box.entry
        self.value.focus_set()

        row = tk.Frame(form, bg=theme.CARD_BG)
        row.pack(fill="x")
        row.grid_columnconfigure((0, 1), weight=1)
        field_label(row, "Öğün").grid(row=0, column=0, sticky="w")
        field_label(row, "Tarih").grid(row=0, column=1, sticky="w", padx=(10, 0))
        self.meal = tk.StringVar(value=self._suggest_meal())
        meal_menu = tk.OptionMenu(row, self.meal, *MEAL_TIPS)
        meal_menu.configure(font=theme.font(9), bg=theme.DARK_FIELD, fg=theme.TEXT,
                            activebackground=theme.PRIMARY_DARK, activeforeground="white",
                            relief="flat", highlightthickness=1, highlightbackground=theme.BORDER)
        meal_menu["menu"].configure(bg=theme.CARD_BG, fg=theme.TEXT, activebackground=theme.PRIMARY_DARK)
        meal_menu.grid(row=1, column=0, sticky="ew", pady=(4, 10))
        self.day = theme.date_entry(row)
        self.day.grid(row=1, column=1, sticky="ew", padx=(10, 0), pady=(4, 10))

        row2 = tk.Frame(form, bg=theme.CARD_BG)
        row2.pack(fill="x")
        row2.grid_columnconfigure(0, weight=1)
        field_label(row2, "Saat (SS:DD)").grid(row=0, column=0, sticky="w")
        self.clock = theme.entry(row2, width=12)
        self.clock.insert(0, datetime.datetime.now().strftime("%H:%M"))
        self.clock.grid(row=1, column=0, sticky="ew", pady=(4, 10))

        field_label(form, "Not (opsiyonel)").pack(anchor="w")
        self.note = theme.entry(form, width=36)
        self.note.pack(fill="x", pady=(4, 14))
        theme.button(form, "Ölçümü Kaydet", self._save, style="primary").pack(fill="x")
        notice(
            left.body,
            "Ölçüm penceresi dışındaki kayıtlar silinmez; ancak ortalama ve insülin hesabına dahil edilmez.",
            accent=theme.AMBER, icon="clock",
        ).pack(fill="x", pady=(12, 0))

        right = tk.Frame(body, bg=theme.APP_BG)
        right.pack(side="left", fill="both", padx=(7, 0))
        right.configure(width=330)
        right.pack_propagate(False)
        schedule = card(right, padx=16, pady=14)
        schedule.pack(fill="x")
        section(schedule.body, "Ölçüm Saatleri", "Daha doğru ortalama için bu aralıkları kullanın.",
                icon="clock", accent=theme.CYAN)
        for meal, (start, end) in sorted(measurement_service.MEAL_WINDOWS.items(), key=lambda kv: kv[1]):
            line = tk.Frame(schedule.body, bg=theme.CARD_BG)
            line.pack(fill="x", pady=3)
            tk.Label(line, text=meal, font=theme.font(9, True), bg=theme.CARD_BG,
                     fg=theme.TEXT, width=9, anchor="w").pack(side="left")
            tk.Label(line, text=f"{start:02d}:00 – {end:02d}:00", font=theme.font(9),
                     bg=theme.CARD_BG, fg=theme.MUTED).pack(side="right")
        tip = card(right, padx=16, pady=14, accent=theme.GREEN)
        tip.pack(fill="x", pady=(12, 0))
        section(tip.body, "Bugünün Özeti", "Kayıtlarınızın kısa görünümü", icon="chart", accent=theme.GREEN)
        self.today_box = tk.Frame(tip.body, bg=theme.CARD_BG)
        self.today_box.pack(fill="x")
        self._render_today()

    def _suggest_meal(self) -> str:
        hour = datetime.datetime.now().hour
        if hour < 10:
            return "Sabah"
        if hour < 14:
            return "Öğle"
        if hour < 17:
            return "İkindi"
        if hour < 21:
            return "Akşam"
        return "Gece"

    def _build_metrics(self) -> None:
        series = records_db.measurement_series(state.session.patient_id, limit=100)
        values = [m["kan_sekeri_degeri"] for m in series]
        today = records_db.recent_measurements(state.session.patient_id, limit=200)
        today_count = sum(1 for m in today if m["olcum_tarihi"] == datetime.date.today())
        avg = sum(values) / len(values) if values else None
        db = get_db()
        profile = ref.find_patient_profile(db, state.session.patient_id) or {} if db is not None else {}
        target = f"{profile.get('hedef_kan_sekeri_min', 70)}–{profile.get('hedef_kan_sekeri_max', 140)}"
        box = tk.Frame(self.body, bg=theme.APP_BG)
        box.pack(fill="x", pady=(0, 12))
        cards = [
            metric(box, icon="droplet", title="Son Ölçüm", value=_num(values[-1] if values else None),
                   accent=theme.BLOOD, note="Kan şekeri"),
            metric(box, icon="chart", title="Genel Ortalama", value=_num(avg),
                   accent=theme.PRIMARY, note=f"{len(values)} ölçüm"),
            metric(box, icon="calendar", title="Bugün", value=today_count,
                   accent=theme.CYAN, note="Ölçüm kaydı"),
            metric(box, icon="target", title="Hedef Aralık", value=target,
                   accent=theme.GREEN, note="mg/dL"),
        ]
        stat_grid(box, cards, columns=4)

    def _render_today(self) -> None:
        for widget in self.today_box.winfo_children():
            widget.destroy()
        rows = [
            m for m in records_db.recent_measurements(state.session.patient_id, limit=100)
            if m["olcum_tarihi"] == datetime.date.today()
        ]
        if not rows:
            tk.Label(self.today_box, text="Bugün henüz ölçüm yok.", font=theme.font(9),
                     bg=theme.CARD_BG, fg=theme.MUTED, anchor="w").pack(fill="x", pady=4)
            return
        for m in rows[:4]:
            line = tk.Frame(self.today_box, bg=theme.CARD_BG)
            line.pack(fill="x", pady=2)
            tk.Label(line, text=m["olcum_tipi"], font=theme.font(8, True), bg=theme.CARD_BG,
                     fg=theme.MUTED, width=8, anchor="w").pack(side="left")
            tk.Label(line, text=f"{m['kan_sekeri_degeri']:g}", font=theme.font(10, True),
                     bg=theme.CARD_BG, fg=theme.BLOOD).pack(side="right")
            tk.Label(line, text=m["olcum_saati"].strftime("%H:%M") if m["olcum_saati"] else "—",
                     font=theme.font(8), bg=theme.CARD_BG, fg=theme.MUTED).pack(side="right", padx=(0, 8))
        if len(rows) > 4:
            tk.Label(self.today_box, text=f"+ {len(rows) - 4} ölçüm daha", font=theme.font(8),
                     bg=theme.CARD_BG, fg=theme.MUTED, anchor="w").pack(fill="x", pady=(4, 0))

    def _save(self) -> None:
        try:
            value = float(self.value.get().strip().replace(",", "."))
        except ValueError:
            messagebox.showerror("Ölçüm", "Sayısal bir değer giriniz.", parent=self)
            return
        try:
            clock = datetime.datetime.strptime(self.clock.get().strip(), "%H:%M").time()
        except ValueError:
            messagebox.showerror("Ölçüm", "Saati SS:DD biçiminde giriniz (örn. 08:15).", parent=self)
            return
        dt = datetime.datetime.combine(self.day.get_date(), clock)
        result = measurement_service.insert_measurement(
            state.session.patient_id, value=value, olcum_tipi=self.meal.get(),
            dt=dt, notlar=self.note.get().strip(),
        )
        if not result["ok"]:
            messagebox.showerror("Ölçüm", result["mesaj"], parent=self)
            return
        if result.get("gecerli"):
            messagebox.showinfo("Ölçüm", result["mesaj"], parent=self)
        else:
            messagebox.showwarning("Saat dışı ölçüm", result["mesaj"], parent=self)
        self.value.delete(0, tk.END)
        self.note.delete(0, tk.END)
        self.app.navigate("measure")

    def refresh(self) -> None:
        self.app.navigate("measure")
