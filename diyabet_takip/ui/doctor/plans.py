"""Doktor — hastaya diyet/egzersiz planı ve belirti atama ekranları."""

from __future__ import annotations

import datetime
import tkinter as tk
from tkinter import messagebox

import tkcalendar

from ... import state, theme
from ...db import doctors as doctors_db
from ...db import reference as ref
from ...db.client import get_db
from .. import helpers


def show_add_to_system_options() -> None:
    win = helpers.modal_window(None, "Hastaya Kayıt Ekle", "640x420")
    helpers.header(
        win, "🗂️ Hastaya Plan / Belirti Ata", "Önce hastayı T.C. ile seçin, sonra tür seçin"
    )

    card = theme.frame(win, card=True)
    card.pack(fill="x", padx=20, pady=(0, 12))
    form = theme.frame(card)
    form.pack(padx=12, pady=12)

    tc_entry = theme.entry(form)
    helpers.form_row(form, 0, "Hasta T.C. Kimlik No:", tc_entry)

    theme.label(
        card,
        "Not: Bu ekrandan atanan belirti kayıtları hastanın geçmişinde "
        "\"Doktor Girişi\" olarak görünür.",
        9,
        fg=theme.MUTED,
    ).pack(anchor="w", padx=16, pady=(0, 10))

    actions = theme.frame(win)
    actions.pack(fill="both", expand=True, padx=20, pady=6)

    tiles = theme.frame(actions)
    tiles.pack(expand=True, fill="both")
    tiles.grid_columnconfigure((0, 1, 2), weight=1)

    def _tc() -> str:
        return tc_entry.get().strip()

    def _hasta(_ekran: str) -> object | None:
        db = get_db()
        if db is None:
            return None
        hasta_id = ref.find_patient_id_by_tc(db, _tc())
        if not hasta_id:
            messagebox.showerror(
                "Hata", "Bu T.C. Kimlik No ile hasta bulunamadı.", parent=win
            )
            return None
        return hasta_id

    def diet_screen() -> None:
        hasta_id = _hasta("Diyet")
        if not hasta_id:
            return
        _diet_assign_window(win, hasta_id)

    def exercise_screen() -> None:
        hasta_id = _hasta("Egzersiz")
        if not hasta_id:
            return
        _exercise_assign_window(win, hasta_id)

    def symptom_screen() -> None:
        hasta_id = _hasta("Belirti")
        if not hasta_id:
            return
        _symptom_assign_window(win, hasta_id)

    tiles_button_data = (
        ("🥗", "Diyet Planı", diet_screen),
        ("🏃", "Egzersiz Planı", exercise_screen),
        ("🤕", "Belirti Girişi", symptom_screen),
    )
    for index, (icon, text, cmd) in enumerate(tiles_button_data):
        cell = theme.frame(tiles, card=True)
        cell.grid(row=0, column=index, padx=10, pady=10, sticky="nsew", ipadx=4)
        tk.Label(cell, text=icon, font=("Segoe UI Emoji", 24), bg=theme.CARD_BG).pack(
            pady=(18, 6)
        )
        tk.Label(
            cell, text=text, font=theme.font(10, True), bg=theme.CARD_BG, fg=theme.TEXT
        ).pack(pady=(0, 18))
        cell.bind("<Button-1>", lambda e, c=cmd: c())
        for child in cell.winfo_children():
            child.bind("<Button-1>", lambda e, c=cmd: c())


def _check_dates(win, bas, bit, sureli: bool) -> tuple[datetime.date, datetime.date | None]:
    start = bas.get_date()
    if sureli:
        return start, bit.get_date()
    return start, None


def _diet_assign_window(parent, hasta_id) -> None:
    db = get_db()
    if db is None:
        return
    win = helpers.modal_window(parent, "Diyet Planı Ata", "520x430")
    helpers.header(win, "🥗 Diyet Planı Ata")

    card = theme.frame(win, card=True)
    card.pack(fill="x", padx=18, pady=(0, 10))
    form = theme.frame(card)
    form.pack(padx=10, pady=10)

    diyet_menu, diyet_var = helpers.dropdown(form, [], width=30)
    options = ref.get_diet_types()  # [(id, ad), ...]
    names = [o[1] for o in options]
    if names:
        diyet_menu["menu"].delete(0, "end")
        for name in names:
            diyet_menu["menu"].add_command(
                label=name, command=lambda n=name: diyet_var.set(n)
            )
    helpers.form_row(form, 0, "Diyet Türü:", diyet_menu)

    bas = tkcalendar.DateEntry(form, width=14, date_pattern="dd.mm.yyyy", firstweekday="sunday")
    helpers.form_row(form, 1, "Başlangıç Tarihi:", bas)
    bit = tkcalendar.DateEntry(form, width=14, date_pattern="dd.mm.yyyy", firstweekday="sunday")
    helpers.form_row(form, 2, "Bitiş Tarihi:", bit)
    sureli = tk.BooleanVar()
    tk.Checkbutton(
        form, text="Bitiş tarihi tanımlı (süresiz plan için işareti kaldırın)",
        variable=sureli, bg=form["bg"], font=theme.font(9),
    ).grid(row=0, column=2, sticky="w", padx=(8, 0))
    sureli.set(True)

    def save() -> None:
        diyet_id = next((o[0] for o in options if o[1] == diyet_var.get()), None)
        if diyet_id is None:
            messagebox.showerror("Hata", "Diyet türü seçiniz.", parent=win)
            return
        start, end = _check_dates(win, bas, bit, sureli.get())
        if end and end < start:
            messagebox.showerror("Hata", "Bitiş tarihi başlangıçtan önce olamaz.", parent=win)
            return
        ok = doctors_db.assign_diet_plan(
            state.session.doctor_id, hasta_id, diyet_id, start, end
        )
        if ok:
            messagebox.showinfo("Başarı", "Diyet planı hastaya atandı.", parent=win)
            win.destroy()
        else:
            messagebox.showerror("Hata", "Plan kaydedilemedi.", parent=win)

    theme.button(card, "Planı Ata", save).pack(fill="x", padx=14, pady=(6, 14), ipady=4)


def _exercise_assign_window(parent, hasta_id) -> None:
    win = helpers.modal_window(parent, "Egzersiz Planı Ata", "520x500")
    helpers.header(win, "🏃 Egzersiz Planı Ata")

    card = theme.frame(win, card=True)
    card.pack(fill="x", padx=18, pady=(0, 10))
    form = theme.frame(card)
    form.pack(padx=10, pady=10)

    egz_menu, egz_var = helpers.dropdown(form, [], width=30)
    options = ref.get_exercise_types()
    names = [o[1] for o in options]
    if names:
        egz_menu["menu"].delete(0, "end")
        for name in names:
            egz_menu["menu"].add_command(label=name, command=lambda n=name: egz_var.set(n))
    helpers.form_row(form, 0, "Egzersiz Türü:", egz_menu)

    siklik = tk.Spinbox(form, from_=1, to=7, width=10, font=theme.font(10))
    siklik.delete(0, tk.END)
    siklik.insert(0, 3)
    helpers.form_row(form, 1, "Haftalık Sıklık (gün):", siklik)

    sure = tk.Spinbox(form, from_=5, to=180, width=10, font=theme.font(10), increment=5)
    sure.delete(0, tk.END)
    sure.insert(0, 30)
    helpers.form_row(form, 2, "Oturum Süresi (dk):", sure)

    bas = tkcalendar.DateEntry(form, width=14, date_pattern="dd.mm.yyyy", firstweekday="sunday")
    helpers.form_row(form, 3, "Başlangıç Tarihi:", bas)
    bit = tkcalendar.DateEntry(form, width=14, date_pattern="dd.mm.yyyy", firstweekday="sunday")
    helpers.form_row(form, 4, "Bitiş Tarihi:", bit)
    sureli = tk.BooleanVar(value=True)
    tk.Checkbutton(
        form, text="Bitiş tarihi tanımlı (süresiz plan için işareti kaldırın)",
        variable=sureli, bg=form["bg"], font=theme.font(9),
    ).grid(row=0, column=2, sticky="w", padx=(8, 0))

    def save() -> None:
        egz_id = next((o[0] for o in options if o[1] == egz_var.get()), None)
        if egz_id is None:
            messagebox.showerror("Hata", "Egzersiz türü seçiniz.", parent=win)
            return
        start, end = _check_dates(win, bas, bit, sureli.get())
        if end and end < start:
            messagebox.showerror("Hata", "Bitiş tarihi başlangıçtan önce olamaz.", parent=win)
            return
        ok = doctors_db.assign_exercise_plan(
            state.session.doctor_id,
            hasta_id,
            egz_id,
            start,
            end,
            int(siklik.get()),
            int(sure.get()),
        )
        if ok:
            messagebox.showinfo("Başarı", "Egzersiz planı hastaya atandı.", parent=win)
            win.destroy()
        else:
            messagebox.showerror("Hata", "Plan kaydedilemedi.", parent=win)

    theme.button(card, "Planı Ata", save).pack(fill="x", padx=14, pady=(6, 14), ipady=4)


def _symptom_assign_window(parent, hasta_id) -> None:
    win = helpers.modal_window(parent, "Belirti Girişi (Doktor)", "620x560")
    helpers.header(win, "🤕 Belirti Girişi", "Birden fazla belirti seçebilirsiniz")

    options = ref.get_symptom_options()

    card = theme.frame(win, card=True)
    card.pack(fill="both", expand=True, padx=18, pady=(0, 10))
    inner = theme.frame(card)
    inner.pack(padx=10, pady=10, fill="both", expand=True)

    theme.label(inner, "Belirtiler (Ctrl ile çoklu seçim):", 10).grid(
        row=0, column=0, sticky="w"
    )
    listbox = tk.Listbox(
        inner,
        selectmode="extended",
        height=6,
        font=theme.font(10),
        bg="white",
        relief="flat",
        highlightthickness=1,
        highlightbackground=theme.BORDER,
    )
    for _symptom_id, ad in options:
        listbox.insert("end", ad)
    listbox.grid(row=0, column=1, columnspan=2, sticky="ew", padx=(6, 0))
    inner.grid_columnconfigure(1, weight=1)

    siddet_menu, siddet_var = helpers.dropdown(
        inner, ("Hafif", "Orta", "Şiddetli"), width=18
    )
    helpers.form_row(inner, 1, "Şiddet Seviyesi:", siddet_menu)

    notlar_entry = theme.entry(inner)
    helpers.form_row(inner, 2, "Açıklama / Not:", notlar_entry)

    tarih_entry = tkcalendar.DateEntry(
        inner, width=14, date_pattern="dd.mm.yyyy", firstweekday="sunday"
    )
    helpers.form_row(inner, 3, "Kayıt Tarihi:", tarih_entry)

    def save() -> None:
        selection = listbox.curselection()
        if not selection:
            messagebox.showerror("Hata", "En az bir belirti seçiniz.", parent=win)
            return
        belirti_ids = [options[i][0] for i in selection]
        saved = doctors_db.assign_symptoms(
            state.session.doctor_id,
            hasta_id,
            tarih_entry.get_date(),
            siddet_var.get(),
            notlar_entry.get().strip(),
            belirti_ids,
        )
        messagebox.showinfo("Başarı", f"{saved} belirti kaydı işlendi.", parent=win)
        win.destroy()

    theme.button(card, "Kaydet", save).pack(fill="x", padx=14, pady=(6, 14), ipady=4)
