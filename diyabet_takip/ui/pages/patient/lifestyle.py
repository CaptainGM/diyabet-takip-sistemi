"""Hasta — günlük diyet/egzersiz kaydı ve belirti takibi."""

from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk

from .... import state, theme
from ....db import patients as patients_db
from ....db import records as records_db
from ....db import reference as ref
from ..base import Page, card, field_label, notice, section, segmented, table
from ._common import _yes


class LifestylePage(Page):
    title = "Diyet & Egzersiz"
    subtitle = "Günlük beslenme ve hareket durumunuzu kaydedin, belirtilerinizi takip edin."
    icon = "apple"
    accent = theme.GREEN

    def __init__(self, parent, app, tab: str = "diet") -> None:
        self.initial_tab = tab
        self.active_tab = tab
        super().__init__(parent, app)

    def build(self) -> None:
        self.page_head(actions=(theme.button(self, "Uyum Takibi", lambda: self.app.navigate("compliance"), style="ghost"),))
        bar, _ = segmented(
            self.body,
            (("diet", "Diyet & Egzersiz"), ("symptom", "Belirti Takibi")),
            active=self.initial_tab,
            command=self._switch,
        )
        bar.pack(anchor="w", pady=(0, 12))
        self.content = tk.Frame(self.body, bg=theme.APP_BG)
        self.content.pack(fill="both", expand=True)
        self._build_content()

    def _switch(self, key: str) -> None:
        self.active_tab = key
        self._build_content()

    def _build_content(self) -> None:
        for widget in self.content.winfo_children():
            widget.destroy()
        if self.active_tab == "symptom":
            self._build_symptom()
        else:
            self._build_diet()

    def _build_diet(self) -> None:
        left = card(self.content, padx=18, pady=14, accent=theme.GREEN)
        left.pack(side="left", fill="both", expand=True, padx=(0, 6))
        section(left.body, "Günlük Durum", "Bugünkü beslenme ve egzersiz kaydınız", icon="apple", accent=theme.GREEN)
        diet = records_db.active_diet_plan(state.session.patient_id)
        exercise = records_db.active_exercise_plan(state.session.patient_id)
        if diet or exercise:
            plan = tk.Frame(left.body, bg=theme.CARD_2, highlightbackground=theme.BORDER, highlightthickness=1)
            plan.pack(fill="x", pady=(0, 12))
            tk.Label(plan, text="Aktif planınız", font=theme.font(8, True), bg=theme.CARD_2,
                     fg=theme.MUTED).pack(anchor="w", padx=10, pady=(8, 2))
            tk.Label(plan, text=diet["diyet_adi"] if diet else "Diyet planı yok", font=theme.font(9),
                     bg=theme.CARD_2, fg=theme.TEXT).pack(anchor="w", padx=10)
            tk.Label(plan, text=(f"{exercise['egzersiz_adi']} · haftada {exercise['haftalik_siklik']} kez"
                                 if exercise else "Egzersiz planı yok"), font=theme.font(9),
                     bg=theme.CARD_2, fg=theme.TEXT).pack(anchor="w", padx=10, pady=(0, 8))
        form = tk.Frame(left.body, bg=theme.CARD_BG)
        form.pack(fill="x")
        field_label(form, "Takip tarihi").pack(anchor="w")
        self.day = theme.date_entry(form)
        self.day.pack(fill="x", pady=(3, 10))
        row = tk.Frame(form, bg=theme.CARD_BG)
        row.pack(fill="x", pady=(0, 10))
        row.grid_columnconfigure((0, 1), weight=1)
        field_label(row, "Diyet uygulandı mı?").grid(row=0, column=0, sticky="w")
        field_label(row, "Egzersiz yapıldı mı?").grid(row=0, column=1, sticky="w", padx=(10, 0))
        self.diet = tk.StringVar(value="Evet")
        self.exercise = tk.StringVar(value="Evet")
        for index, var in enumerate((self.diet, self.exercise)):
            menu = tk.OptionMenu(row, var, "Evet", "Hayır")
            menu.configure(font=theme.font(9), bg=theme.DARK_FIELD, fg=theme.TEXT,
                           activebackground=theme.PRIMARY_DARK, relief="flat",
                           highlightthickness=1, highlightbackground=theme.BORDER)
            menu["menu"].configure(bg=theme.CARD_BG, fg=theme.TEXT, activebackground=theme.PRIMARY_DARK)
            menu.grid(row=1, column=index, sticky="ew", pady=(3, 0), padx=(0, 10) if index == 0 else (10, 0))
        field_label(form, "Egzersiz süresi (dk)").pack(anchor="w")
        self.duration = theme.spinbox(form, from_=0, to=300, width=10, increment=5)
        default_duration = exercise["sure_dakika"] if exercise else 30
        self.duration.delete(0, tk.END)
        self.duration.insert(0, default_duration)
        self.duration.pack(fill="x", pady=(3, 10))
        field_label(form, "Not").pack(anchor="w")
        self.note = theme.entry(form, width=34)
        self.note.pack(fill="x", pady=(3, 14))
        theme.button(form, "Kaydı Tamamla", self._save_diet, style="primary").pack(fill="x")
        notice(left.body, "Diyet ve egzersiz kayıtları uyum skorunuza yansır.",
               accent=theme.GREEN, icon="target").pack(fill="x", pady=(12, 0))

        right = card(self.content, padx=14, pady=12)
        right.pack(side="left", fill="both", expand=True, padx=(6, 0))
        section(right.body, "Son 7 Gün", "Diyet ve egzersiz geçmişi", icon="calendar", accent=theme.CYAN)
        tree, wrap = table(
            right.body,
            ("tarih", "diyet", "egz", "sure"),
            ("Tarih", "Diyet", "Egzersiz", "Süre"),
            (110, 140, 140, 110), height=9,
        )
        wrap.pack(fill="both", expand=True)
        for idx, row in enumerate(records_db.diet_exercise_history(state.session.patient_id, limit=7)):
            tree.insert("", "end", tags=("odd" if idx % 2 else "even",), values=(
                row["takip_tarihi"].strftime("%d.%m.%Y"), _yes(row["diyet_uygulandimi"]),
                _yes(row["egzersiz_yapildimi"]), f"{row['sure_dakika']} dk" if row["sure_dakika"] is not None else "—",
            ))

    def _save_diet(self) -> None:
        day = self.day.get_date()
        patients_db.upsert_diet_log(
            state.session.patient_id, day, self.diet.get() == "Evet", self.note.get().strip()
        )
        patients_db.upsert_exercise_log(
            state.session.patient_id, day, self.exercise.get() == "Evet",
            int(self.duration.get()), self.note.get().strip(),
        )
        messagebox.showinfo("Kayıt", f"{day.strftime('%d.%m.%Y')} tarihli kaydınız güncellendi.", parent=self)
        self.app.navigate("lifestyle", tab="diet")

    def _build_symptom(self) -> None:
        options = ref.get_symptom_options()
        left = card(self.content, padx=18, pady=14, accent=theme.ORANGE)
        left.pack(side="left", fill="both", expand=True, padx=(0, 6))
        section(left.body, "Belirti Kaydı", "Birden fazla belirti seçebilirsiniz.", icon="bandage", accent=theme.ORANGE)
        field_label(left.body, "Belirtiler (Ctrl ile çoklu seçim)").pack(anchor="w")
        box = tk.Frame(left.body, bg=theme.CARD_BG)
        box.pack(fill="both", expand=True, pady=(3, 10))
        self.symptom_list = theme.listbox(box, selectmode="extended", height=8, exportselection=False)
        for _sid, name in options:
            self.symptom_list.insert("end", name)
        self.symptom_list.pack(side="left", fill="both", expand=True)
        scroll = ttk.Scrollbar(box, orient="vertical", command=self.symptom_list.yview)
        self.symptom_list.configure(yscrollcommand=scroll.set)
        scroll.pack(side="right", fill="y")
        row = tk.Frame(left.body, bg=theme.CARD_BG)
        row.pack(fill="x", pady=(0, 8))
        row.grid_columnconfigure((0, 1), weight=1)
        field_label(row, "Şiddet").grid(row=0, column=0, sticky="w")
        field_label(row, "Tarih").grid(row=0, column=1, sticky="w", padx=(10, 0))
        self.severity = tk.StringVar(value="Orta")
        sev = tk.OptionMenu(row, self.severity, "Hafif", "Orta", "Şiddetli")
        sev.configure(font=theme.font(9), bg=theme.DARK_FIELD, fg=theme.TEXT,
                      activebackground=theme.PRIMARY_DARK, relief="flat",
                      highlightthickness=1, highlightbackground=theme.BORDER)
        sev["menu"].configure(bg=theme.CARD_BG, fg=theme.TEXT, activebackground=theme.PRIMARY_DARK)
        sev.grid(row=1, column=0, sticky="ew", pady=(3, 0), padx=(0, 10))
        self.symptom_day = theme.date_entry(row)
        self.symptom_day.grid(row=1, column=1, sticky="ew", padx=(10, 0), pady=(3, 0))
        field_label(left.body, "Not").pack(anchor="w")
        self.symptom_note = theme.entry(left.body, width=34)
        self.symptom_note.pack(fill="x", pady=(3, 12))
        theme.button(left.body, "Belirtiyi Kaydet", self._save_symptom, style="primary").pack(fill="x")
        notice(left.body, "Belirti kayıtları doktorunuzun hasta detay ekranında görünür.",
               accent=theme.ORANGE, icon="stethoscope").pack(fill="x", pady=(12, 0))

        right = card(self.content, padx=14, pady=12)
        right.pack(side="left", fill="both", expand=True, padx=(6, 0))
        section(right.body, "Belirti Geçmişi", "Son 30 gün", icon="report", accent=theme.ORANGE)
        tree, wrap = table(
            right.body,
            ("tarih", "belirti", "siddet", "kaydeden"),
            ("Tarih", "Belirti", "Şiddet", "Kaydeden"),
            (105, 170, 100, 150), height=10,
        )
        wrap.pack(fill="both", expand=True)
        for idx, row in enumerate(records_db.symptom_history(state.session.patient_id, limit=30)):
            tree.insert("", "end", tags=("odd" if idx % 2 else "even",), values=(
                row["kayit_tarihi"].strftime("%d.%m.%Y"), row["belirti_adi"],
                row["siddet_seviyesi"] or "—", row["kaydeden"],
            ))

    def _save_symptom(self) -> None:
        options = ref.get_symptom_options()
        selection = self.symptom_list.curselection()
        if not selection:
            messagebox.showinfo("Belirti", "En az bir belirti seçin.", parent=self)
            return
        saved = patients_db.record_symptoms_by_patient(
            state.session.patient_id, self.symptom_day.get_date(), self.severity.get(),
            self.symptom_note.get().strip(), [options[i][0] for i in selection],
        )
        messagebox.showinfo("Belirti", f"{saved} belirti kaydı işlendi.", parent=self)
        self.app.navigate("lifestyle", tab="symptom")

    def refresh(self) -> None:
        self.app.navigate("lifestyle", tab=self.active_tab)
