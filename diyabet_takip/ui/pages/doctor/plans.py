"""Doktor — diyet, egzersiz ve belirti planı atama."""

from __future__ import annotations

import datetime
import tkinter as tk
from tkinter import messagebox, ttk

from .... import state, theme
from ....db import doctors as doctors_db
from ....db import records as records_db
from ....db import reference as ref
from ... import icons
from ..base import Page, card, empty, field_label, section, segmented


class PlansPage(Page):
    title = "Plan / Belirti"
    subtitle = "Hastaya diyet, egzersiz ve belirti kayıtları ekleyin."
    icon = "clipboard"
    accent = theme.PURPLE

    def build(self) -> None:
        self.page_head()
        patients = doctors_db.list_patients_for_doctor(state.session.doctor_id)
        self.patient_map = {f"{p['ad']} {p['soyad']} · {p['tc_kimlik_no']}": p for p in patients}
        self.patient_var = tk.StringVar(value=next(iter(self.patient_map), "Hasta yok"))
        self.patient_var.trace_add("write", lambda *_: self._refresh_plan())

        selector = card(self.body, padx=16, pady=12, accent=theme.PURPLE)
        selector.pack(fill="x", pady=(0, 12))
        row = tk.Frame(selector.body, bg=theme.CARD_BG)
        row.pack(fill="x")
        icons.badge(row, "clipboard", theme.PURPLE, size=36, bg=theme.CARD_BG).pack(side="left", padx=(0, 10))
        tk.Label(row, text="Hasta seçin", font=theme.font(8), bg=theme.CARD_BG,
                 fg=theme.MUTED).pack(anchor="w")
        menu = tk.OptionMenu(row, self.patient_var, *(self.patient_map.keys() or ["Hasta yok"]))
        menu.configure(font=theme.font(9), bg=theme.DARK_FIELD, fg=theme.TEXT,
                       activebackground=theme.PRIMARY_DARK, relief="flat",
                       highlightthickness=1, highlightbackground=theme.BORDER, width=36)
        menu["menu"].configure(bg=theme.CARD_BG, fg=theme.TEXT, activebackground=theme.PRIMARY_DARK)
        menu.pack(side="left", padx=(12, 20), pady=(3, 0))
        self.plan_summary = tk.Frame(row, bg=theme.CARD_BG)
        self.plan_summary.pack(side="left", fill="x", expand=True)

        body = tk.Frame(self.body, bg=theme.APP_BG)
        body.pack(fill="both", expand=True)
        left = card(body, padx=14, pady=12)
        left.pack(side="left", fill="both", padx=(0, 6))
        left.configure(width=330)
        left.pack_propagate(False)
        section(left.body, "Aktif Planlar", "Hastanın güncel takip planı",
                icon="target", accent=theme.GREEN)
        self.plans_box = tk.Frame(left.body, bg=theme.CARD_BG)
        self.plans_box.pack(fill="both", expand=True)

        right = card(body, padx=16, pady=14)
        right.pack(side="left", fill="both", expand=True, padx=(6, 0))
        self.assignment_box = tk.Frame(right.body, bg=theme.CARD_BG)
        self.assignment_box.pack(fill="both", expand=True)
        bar, _ = segmented(
            self.assignment_box,
            (("diet", "Diyet"), ("exercise", "Egzersiz"), ("symptom", "Belirti")),
            active="diet",
            command=self._show_form,
        )
        bar.pack(anchor="w", pady=(0, 12))
        self.form_host = tk.Frame(self.assignment_box, bg=theme.CARD_BG)
        self.form_host.pack(fill="both", expand=True)
        self._show_form("diet")
        self._refresh_plan()

    def _patient(self) -> dict | None:
        return self.patient_map.get(self.patient_var.get())

    def _refresh_plan(self) -> None:
        if not hasattr(self, "plans_box"):
            return
        for widget in self.plans_box.winfo_children():
            widget.destroy()
        patient = self._patient()
        if not patient:
            empty(self.plans_box, "Hasta seçin.", icon="users").pack(fill="both", expand=True)
            return
        pid = patient["hasta_id"]
        diet = records_db.active_diet_plan(pid)
        exercise = records_db.active_exercise_plan(pid)
        for title, value, sub, accent, icon_name in (
            ("Diyet Planı", diet["diyet_adi"] if diet else "Plan yok",
             (diet or {}).get("aciklama") or "Henüz aktif diyet planı yok.", theme.GREEN, "apple"),
            ("Egzersiz Planı", exercise["egzersiz_adi"] if exercise else "Plan yok",
             f"Haftada {exercise['haftalik_siklik']} kez · {exercise['sure_dakika']} dk"
             if exercise else "Henüz aktif egzersiz planı yok.", theme.ORANGE, "dumbbell"),
        ):
            box = tk.Frame(self.plans_box, bg=theme.CARD_2, highlightbackground=theme.BORDER,
                           highlightthickness=1)
            box.pack(fill="x", pady=4)
            top = tk.Frame(box, bg=theme.CARD_2)
            top.pack(fill="x", padx=10, pady=(9, 2))
            icons.badge(top, icon_name, accent, size=28, bg=theme.CARD_2).pack(side="left", padx=(0, 8))
            tk.Label(top, text=title, font=theme.font(8, True), bg=theme.CARD_2,
                     fg=theme.MUTED).pack(anchor="w")
            tk.Label(top, text=value, font=theme.font(11, True), bg=theme.CARD_2,
                     fg=theme.TEXT).pack(anchor="w")
            tk.Label(box, text=sub, font=theme.font(8), bg=theme.CARD_2, fg=theme.MUTED,
                     anchor="w", wraplength=280, justify="left").pack(
                fill="x", padx=10, pady=(4, 9)
            )
        sym = records_db.doctor_symptom_records_for_patient(pid, days=30)
        tk.Label(self.plans_box, text=f"Son 30 gün: {len(sym)} belirti kaydı",
                 font=theme.font(8), bg=theme.CARD_BG, fg=theme.MUTED).pack(
            anchor="w", pady=(10, 0)
        )

    def _show_form(self, kind: str) -> None:
        for widget in self.form_host.winfo_children():
            widget.destroy()
        patient = self._patient()
        if not patient:
            empty(self.form_host, "Hasta seçin.", icon="users").pack(fill="both", expand=True)
            return
        if kind == "diet":
            self._diet_form(patient)
        elif kind == "exercise":
            self._exercise_form(patient)
        else:
            self._symptom_form(patient)

    def _diet_form(self, patient: dict) -> None:
        section(self.form_host, "Diyet Planı Ata", "Hastanın beslenme takibini başlatın.",
                icon="apple", accent=theme.GREEN)
        form = tk.Frame(self.form_host, bg=theme.CARD_BG)
        form.pack(fill="x")
        options = ref.get_diet_types()
        names = [o[1] for o in options]
        field_label(form, "Diyet türü").pack(anchor="w")
        var = tk.StringVar(value=names[0] if names else "")
        menu = tk.OptionMenu(form, var, *(names or ["Kayıt yok"]))
        menu.configure(font=theme.font(9), bg=theme.DARK_FIELD, fg=theme.TEXT,
                       activebackground=theme.PRIMARY_DARK, relief="flat",
                       highlightthickness=1, highlightbackground=theme.BORDER)
        menu.pack(fill="x", pady=(3, 10))
        field_label(form, "Başlangıç").pack(anchor="w")
        start = theme.date_entry(form)
        start.pack(fill="x", pady=(3, 10))
        field_label(form, "Bitiş tarihi").pack(anchor="w")
        end = theme.date_entry(form)
        end.set_date(datetime.date.today() + datetime.timedelta(days=365))
        end.pack(fill="x", pady=(3, 12))
        def save() -> None:
            chosen = next((o[0] for o in options if o[1] == var.get()), None)
            if chosen is None:
                messagebox.showinfo("Diyet", "Diyet türü seçin.", parent=self)
                return
            doctors_db.assign_diet_plan(state.session.doctor_id, patient["hasta_id"], chosen,
                                        start.get_date(), end.get_date())
            messagebox.showinfo("Diyet", "Diyet planı hastaya atandı.", parent=self)
            self._refresh_plan()
        theme.button(self.form_host, "Planı Ata", save, style="primary").pack(anchor="e", pady=(12, 0))

    def _exercise_form(self, patient: dict) -> None:
        section(self.form_host, "Egzersiz Planı Ata", "Haftalık sıklık ve süreyi belirleyin.",
                icon="dumbbell", accent=theme.ORANGE)
        form = tk.Frame(self.form_host, bg=theme.CARD_BG)
        form.pack(fill="x")
        options = ref.get_exercise_types()
        names = [o[1] for o in options]
        field_label(form, "Egzersiz türü").pack(anchor="w")
        var = tk.StringVar(value=names[0] if names else "")
        menu = tk.OptionMenu(form, var, *(names or ["Kayıt yok"]))
        menu.configure(font=theme.font(9), bg=theme.DARK_FIELD, fg=theme.TEXT,
                       activebackground=theme.PRIMARY_DARK, relief="flat",
                       highlightthickness=1, highlightbackground=theme.BORDER)
        menu.pack(fill="x", pady=(3, 10))
        row = tk.Frame(form, bg=theme.CARD_BG)
        row.pack(fill="x", pady=(0, 10))
        row.grid_columnconfigure((0, 1), weight=1)
        field_label(row, "Haftalık sıklık").grid(row=0, column=0, sticky="w")
        field_label(row, "Süre (dk)").grid(row=0, column=1, sticky="w", padx=(8, 0))
        freq = theme.spinbox(row, from_=1, to=7, width=8)
        freq.delete(0, tk.END)
        freq.insert(0, 3)
        freq.grid(row=1, column=0, sticky="ew", pady=(3, 0))
        duration = theme.spinbox(row, from_=5, to=180, width=8, increment=5)
        duration.delete(0, tk.END)
        duration.insert(0, 30)
        duration.grid(row=1, column=1, sticky="ew", padx=(8, 0), pady=(3, 0))
        field_label(form, "Başlangıç").pack(anchor="w")
        start = theme.date_entry(form)
        start.pack(fill="x", pady=(3, 10))
        field_label(form, "Bitiş tarihi").pack(anchor="w")
        end = theme.date_entry(form)
        end.set_date(datetime.date.today() + datetime.timedelta(days=365))
        end.pack(fill="x", pady=(3, 12))
        def save() -> None:
            chosen = next((o[0] for o in options if o[1] == var.get()), None)
            if chosen is None:
                messagebox.showinfo("Egzersiz", "Egzersiz türü seçin.", parent=self)
                return
            doctors_db.assign_exercise_plan(
                state.session.doctor_id, patient["hasta_id"], chosen, start.get_date(),
                end.get_date(), int(freq.get()), int(duration.get()),
            )
            messagebox.showinfo("Egzersiz", "Egzersiz planı hastaya atandı.", parent=self)
            self._refresh_plan()
        theme.button(self.form_host, "Planı Ata", save, style="primary").pack(anchor="e", pady=(12, 0))

    def _symptom_form(self, patient: dict) -> None:
        section(self.form_host, "Belirti Girişi", "Birden fazla belirti seçebilirsiniz.",
                icon="bandage", accent=theme.ORANGE)
        options = ref.get_symptom_options()
        field_label(self.form_host, "Belirtiler (Ctrl ile çoklu seçim)").pack(anchor="w")
        box = tk.Frame(self.form_host, bg=theme.CARD_BG)
        box.pack(fill="both", expand=True, pady=(3, 10))
        listbox = theme.listbox(box, selectmode="extended", height=6, exportselection=False)
        for _sid, name in options:
            listbox.insert("end", name)
        listbox.pack(side="left", fill="both", expand=True)
        scroll = ttk.Scrollbar(box, orient="vertical", command=listbox.yview)
        listbox.configure(yscrollcommand=scroll.set)
        scroll.pack(side="right", fill="y")
        row = tk.Frame(self.form_host, bg=theme.CARD_BG)
        row.pack(fill="x", pady=(0, 8))
        field_label(row, "Şiddet").pack(anchor="w")
        severity = tk.StringVar(value="Orta")
        sev = tk.OptionMenu(row, severity, "Hafif", "Orta", "Şiddetli")
        sev.configure(font=theme.font(9), bg=theme.DARK_FIELD, fg=theme.TEXT,
                      activebackground=theme.PRIMARY_DARK, relief="flat",
                      highlightthickness=1, highlightbackground=theme.BORDER, width=12)
        sev.pack(anchor="w", pady=(3, 0))
        field_label(self.form_host, "Not").pack(anchor="w")
        note = theme.entry(self.form_host, width=30)
        note.pack(fill="x", pady=(3, 8))
        field_label(self.form_host, "Tarih").pack(anchor="w")
        day = theme.date_entry(self.form_host)
        day.pack(fill="x", pady=(3, 12))
        def save() -> None:
            selection = listbox.curselection()
            if not selection:
                messagebox.showinfo("Belirti", "En az bir belirti seçin.", parent=self)
                return
            saved = doctors_db.assign_symptoms(
                state.session.doctor_id, patient["hasta_id"], day.get_date(),
                severity.get(), note.get().strip(), [options[i][0] for i in selection],
            )
            messagebox.showinfo("Belirti", f"{saved} belirti kaydı işlendi.", parent=self)
            self._refresh_plan()
        theme.button(self.form_host, "Kaydet", save, style="primary").pack(anchor="e")
