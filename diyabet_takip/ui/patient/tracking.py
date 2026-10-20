"""Hasta — diyet/egzersiz durumu, semptom takibi ve uyum skorları."""

from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk

import tkcalendar

from ... import state, theme
from ...db import patients as patients_db
from ...db import records as records_db
from ...db import reference as ref
from .. import charts, helpers


def enter_diet_exercise() -> None:
    """O gün için diyet uygulandı mı / egzersiz yapıld mı kaydı (upsert)."""
    win = helpers.modal_window(None, "Diyet / Egzersiz Durumu Gir", "560x620")
    helpers.header(win, "🥗 Diyet / Egzersiz Takip Formu", "Günlük durumu kaydedin")

    diet_plan = records_db.active_diet_plan(state.session.patient_id)
    ex_plan = records_db.active_exercise_plan(state.session.patient_id)

    # --- Doktor planına öneriler ---------------------------------------------
    plan_card = theme.frame(win, card=True)
    plan_card.pack(fill="x", padx=18, pady=(0, 10))
    theme.label(plan_card, "Doktorunuzun Aktif Planı", 10, bold=True).pack(
        anchor="w", padx=14, pady=(10, 2)
    )
    theme.label(
        plan_card,
        "• Diyet: " + (diet_plan["diyet_adi"] if diet_plan else "kayıt yok"),
        9,
    ).pack(anchor="w", padx=14, pady=2)
    theme.label(
        plan_card,
        "• Egzersiz: "
        + (
            f"{ex_plan['egzersiz_adi']} (haftada {ex_plan['haftalik_siklik']} kez)"
            if ex_plan
            else "kayıt yok"
        ),
        9,
    ).pack(anchor="w", padx=14, pady=2)

    # --- Form ----------------------------------------------------------------
    card = theme.frame(win, card=True)
    card.pack(fill="x", padx=18, pady=(0, 10))
    form = theme.frame(card)
    form.pack(padx=10, pady=10)

    tarih_entry = tkcalendar.DateEntry(form, width=14, date_pattern="dd.mm.yyyy", firstweekday="sunday")
    helpers.form_row(form, 0, "Takip Tarihi:", tarih_entry)

    theme.label(form, "Diyet", 10, bold=True).grid(row=1, column=0, columnspan=2, sticky="w")
    diyet_var = tk.StringVar(value="Evet")
    diyet_menu, _ = helpers.dropdown(form, ("Evet", "Hayır"), width=12)
    diyet_menu["menu"].delete(0, "end")
    for opt in ("Evet", "Hayır"):
        diyet_menu["menu"].add_command(label=opt, command=lambda o=opt: diyet_var.set(o))
    helpers.form_row(form, 2, "Bugün diyete uyuldu mu?", diyet_menu)

    theme.label(form, "Egzersiz", 10, bold=True).grid(row=3, column=0, columnspan=2, sticky="w")
    egz_var = tk.StringVar(value="Evet")
    egz_menu, _ = helpers.dropdown(form, ("Evet", "Hayır"), width=12)
    egz_menu["menu"].delete(0, "end")
    for opt in ("Evet", "Hayır"):
        egz_menu["menu"].add_command(label=opt, command=lambda o=opt: egz_var.set(o))
    helpers.form_row(form, 4, "Bugün egzersiz yapıldı mı?", egz_menu)

    sure_spin = tk.Spinbox(form, from_=0, to=240, width=10, font=theme.font(10), increment=5)
    sure_spin.delete(0, tk.END)
    if ex_plan and ex_plan.get("sure_dakika"):
        sure_spin.insert(0, ex_plan["sure_dakika"])
    else:
        sure_spin.insert(0, 30)
    helpers.form_row(form, 5, "Süre (dk):", sure_spin)

    notlar_entry = theme.entry(form)
    helpers.form_row(form, 6, "Not:", notlar_entry)

    def save() -> None:
        day = tarih_entry.get_date()
        patients_db.upsert_diet_log(
            state.session.patient_id, day, diyet_var.get() == "Evet", notlar_entry.get().strip()
        )
        patients_db.upsert_exercise_log(
            state.session.patient_id,
            day,
            egz_var.get() == "Evet",
            int(sure_spin.get()),
            notlar_entry.get().strip(),
        )
        messagebox.showinfo(
            "Başarılı",
            f"{day.strftime('%d.%m.%Y')} tarihli diyet ve egzersiz kaydınız güncellendi!",
            parent=win,
        )
        win.destroy()

    theme.button(card, "Kaydet", save).pack(fill="x", padx=14, pady=(6, 14), ipady=4)

    # --- Son 7 günü mini özet --------------------------------------------------
    history = records_db.diet_exercise_history(state.session.patient_id, limit=7)
    if history:
        summary = theme.frame(win, card=True)
        summary.pack(fill="x", padx=18, pady=(0, 10))
        theme.label(summary, "Son 7 Gün", 10, bold=True).pack(anchor="w", padx=14, pady=(10, 4))
        for row in history:
            diyet = "✅" if row["diyet_uygulandimi"] else "➖" if row["diyet_uygulandimi"] is None else "❌"
            egz = "✅" if row["egzersiz_yapildimi"] else "➖" if row["egzersiz_yapildimi"] is None else "❌"
            theme.label(
                summary,
                f"{helpers.date_label(row['takip_tarihi'])}:   Diyet {diyet}   "
                f"Egzersiz {egz}  ({row['sure_dakika'] or 0} dk)",
                9,
            ).pack(anchor="w", padx=14, pady=1)


# ---------------------------------------------------------------------------
# Semptom takibi (hasta)
# ---------------------------------------------------------------------------
def enter_symptoms() -> None:
    win = helpers.modal_window(None, "Semptom Takibi Yap", "640x600")
    helpers.header(win, "🤕 Semptom Takibi", "Bugün olan belirtileri kaydedin")

    options = ref.get_symptom_options()

    card = theme.frame(win, card=True)
    card.pack(fill="both", expand=True, padx=18, pady=(0, 10))
    form = theme.frame(card)
    form.pack(padx=10, pady=10, fill="both", expand=True)

    theme.label(form, "Belirtiler (Ctrl ile birden çok seçin):", 10).grid(row=0, column=0, sticky="w")
    listbox = tk.Listbox(
        form,
        selectmode="extended",
        height=7,
        font=theme.font(10),
        bg="white",
        relief="flat",
        highlightthickness=1,
        highlightbackground=theme.BORDER,
    )
    for _symptom_id, ad in options:
        listbox.insert("end", ad)
    listbox.grid(row=0, column=1, columnspan=2, sticky="ew", pady=(4, 8))
    form.grid_columnconfigure(1, weight=1)

    siddet_menu, siddet_var = helpers.dropdown(form, ("Hafif", "Orta", "Şiddetli"), width=16)
    helpers.form_row(form, 1, "Şiddet Seviyesi:", siddet_menu)

    notlar_entry = theme.entry(form)
    helpers.form_row(form, 2, "Ek Bilgi / Not:", notlar_entry)

    tarih_entry = tkcalendar.DateEntry(form, width=14, date_pattern="dd.mm.yyyy", firstweekday="sunday")
    helpers.form_row(form, 3, "Semptom Tarihi:", tarih_entry)

    def save() -> None:
        selection = listbox.curselection()
        if not selection:
            messagebox.showerror("Hata", "En az bir belirti seçmelisiniz.", parent=win)
            return
        belirti_ids = [options[i][0] for i in selection]
        saved = patients_db.record_symptoms_by_patient(
            state.session.patient_id,
            tarih_entry.get_date(),
            siddet_var.get(),
            notlar_entry.get().strip(),
            belirti_ids,
        )
        messagebox.showinfo("Başarılı", f"{saved} belirti kaydı işlendi!", parent=win)
        win.destroy()

    theme.button(card, "Kaydet", save).pack(fill="x", padx=14, pady=(6, 14), ipady=4)


# ---------------------------------------------------------------------------
# Diyet/Egzersiz Uyum Takibi (%)
# ---------------------------------------------------------------------------
def show_patient_compliance() -> None:
    win = helpers.modal_window(None, "Diyet/Egzersiz Uyum Takibi (%)", "960x680")
    helpers.header(
        win, "🎯 Uyum Takibi", "Son 30 günün diyet / egzersiz / ölçüm uyum yüzdesi"
    )

    history = records_db.compliance_history(state.session.patient_id, limit=30)

    stats_bar = theme.frame(win)
    stats_bar.pack(fill="x", padx=16, pady=(0, 10))
    if history:
        latest = history[0]
        for index, (title, key) in enumerate(
            (
                ("Genel Skor", "genel_uyum_skoru"),
                ("Diyet Uyum", "diyet_uyum_orani"),
                ("Egzersiz Uyum", "egzersiz_uyum_orani"),
                ("Ölçüm Uyum", "olcum_uyum_orani"),
            )
        ):
            cell = theme.frame(stats_bar, card=True)
            cell.grid(row=0, column=index, padx=6, pady=6, sticky="nsew")
            stats_bar.grid_columnconfigure(index, weight=1)
            theme.muted_label(cell, title, 9).pack(pady=(10, 0))
            theme.label(
                cell, f"%{latest[key]:g}", 14, bold=True, fg=theme.PRIMARY
            ).pack(pady=(0, 10))

    chart_box = theme.frame(win, card=True)
    chart_box.pack(fill="both", expand=True, padx=16, pady=(0, 10))
    charts.plot_compliance_percentages(chart_box, history, role_for_title="Hasta")

    card = theme.frame(win, card=True)
    card.pack(fill="both", expand=True, padx=16, pady=(0, 12))
    tree = ttk.Treeview(
        card,
        columns=("tarih", "diyet", "egz", "olcum", "genel"),
        show="headings",
        height=8,
        style="Card.Treeview",
    )
    for key, text, width in (
        ("tarih", "Hesap Tarihi", 110),
        ("diyet", "Diyet (% , son 7 gün)", 150),
        ("egz", "Egzersiz (%)", 150),
        ("olcum", "Ölçüm (%)", 150),
        ("genel", "Genel Skor (%)", 150),
    ):
        tree.heading(key, text=text)
        tree.column(key, width=width, anchor="w")
    tree.pack(side="left", fill="both", expand=True, padx=(1, 0), pady=1)
    vsb = ttk.Scrollbar(card, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=vsb.set)
    vsb.pack(side="right", fill="y")

    for row in history:
        tree.insert(
            "",
            "end",
            values=(
                helpers.date_label(row["hesaplama_tarihi"]),
                f"%{row['diyet_uyum_orani']:g}",
                f"%{row['egzersiz_uyum_orani']:g}",
                f"%{row['olcum_uyum_orani']:g}",
                f"%{row['genel_uyum_skoru']:g}",
            ),
        )
