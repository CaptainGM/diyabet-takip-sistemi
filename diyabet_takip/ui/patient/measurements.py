"""Hasta — kan şekeri ölçümü girme + geçmiş/grafik ekranı."""

from __future__ import annotations

import datetime
import tkinter as tk
from tkinter import messagebox, ttk

import tkcalendar

from ... import state, theme
from ...db import records as records_db
from ...db import reference as ref
from ...db.client import get_db
from ...services import measurement_service
from .. import charts, helpers

MEAL_TIPS = ("Sabah", "Öğle", "İkindi", "Akşam", "Gece")


def enter_blood_sugar() -> None:
    """Kan şekeri ölçümü giriş ekranı (saat dışı ölçümlerde bilgilendirme)."""
    win = helpers.modal_window(None, "Kan Şekeri Ölçümü Gir", "540x560")
    helpers.header(
        win, "🩸 Kan Şekeri Ölçümü", "Ölçüm saat aralığına uygunsa ortalamalara dahil olur"
    )

    # Bu ekleme v1 ekranında da vardı: öğün saatleri hatırlatması
    card = theme.frame(win, card=True)
    card.pack(fill="x", padx=18, pady=(0, 10))
    schedule = theme.frame(card)
    schedule.pack(padx=12, pady=10)
    theme.label(schedule, "Hatırlatma — Ölçüm Saat Aralıkları:", 10, bold=True).grid(
        row=0, column=0, columnspan=4, sticky="w"
    )
    windows = measurement_service.MEAL_WINDOWS
    for index, (tip, (start, end)) in enumerate(sorted(windows.items(), key=lambda kv: kv[1])):
        theme.label(schedule, f"{tip}  {start:02d}:00–{end:02d}:00", 9).grid(
            row=1 + index // 4, column=index % 4, padx=6, pady=4
        )

    form_card = theme.frame(win, card=True)
    form_card.pack(fill="x", padx=18, pady=(0, 10))
    form = theme.frame(form_card)
    form.pack(padx=10, pady=10)

    deger_entry = theme.entry(form, width=16)
    deger_entry.focus_set()
    helpers.form_row(form, 0, "Kan Şekeri Değeri (mg/dL):", deger_entry)

    tip_menu, tip_var = helpers.dropdown(form, MEAL_TIPS, width=16)
    now = datetime.datetime.now()
    helpers.form_row(form, 1, "Ölçüm Tipi:", tip_menu)

    tarih_entry = tkcalendar.DateEntry(form, width=14, date_pattern="dd.mm.yyyy", firstweekday="sunday")
    helpers.form_row(form, 2, "Ölçüm Tarihi:", tarih_entry)

    saat_entry = theme.entry(form, width=12)
    saat_entry.insert(0, now.strftime("%H:%M"))
    helpers.form_row(form, 3, "Ölçüm Saati (SS:DAK):", saat_entry)

    notlar_entry = theme.entry(form)
    helpers.form_row(form, 4, "Not (opsiyonel):", notlar_entry)

    theme.muted_label(
        form_card,
        "Not: Saat aralığı dışındaki ölçümler kaydedilir ama ortalama ve "
        "insülin hesaplarına DAHİL EDİLMEZ; hastaya bildirim gider.",
        8,
    ).pack(anchor="w", padx=16, pady=(0, 10))

    def _parse_time(text: str) -> datetime.time | None:
        try:
            return datetime.datetime.strptime(text.strip(), "%H:%M").time()
        except ValueError:
            return None

    def save() -> None:
        text = deger_entry.get().strip().replace(",", ".")
        try:
            value = float(text)
        except ValueError:
            messagebox.showerror("Hata", "Sayısal bir değer giriniz.", parent=win)
            return
        measure_time = _parse_time(saat_entry.get())
        if measure_time is None:
            messagebox.showerror("Hata", "Saati SS:DAK biçiminde giriniz (örn. 08:15).", parent=win)
            return
        dt = datetime.datetime.combine(tarih_entry.get_date(), measure_time)
        result = measurement_service.insert_measurement(
            state.session.patient_id,
            value=value,
            olcum_tipi=tip_var.get(),
            dt=dt,
            notlar=notlar_entry.get().strip(),
        )

        if result["ok"]:
            if result.get("gecerli"):
                messagebox.showinfo("Başarılı", result["mesaj"], parent=win)
                win.destroy()
            else:
                messagebox.showwarning("Saat Dışı Ölçüm", result["mesaj"], parent=win)
                win.destroy()
        else:
            messagebox.showerror("Hata", result["mesaj"], parent=win)

    theme.button(form_card, "Ölçümü Kaydet", save).pack(
        fill="x", padx=14, pady=(6, 14), ipady=4
    )


# ---------------------------------------------------------------------------
# Geçmiş + grafikler
# ---------------------------------------------------------------------------
def show_blood_sugar_history_and_graphs() -> None:
    win = helpers.modal_window(None, "Kan Şekeri Geçmişi ve Grafikler", "1000x720")
    helpers.header(win, "📈 Kan Şekeri Geçmişi", "Son ölçümler + değişim grafiği")

    db = get_db()
    if db is None:
        return
    profile = ref.find_patient_profile(db, state.session.patient_id) or {}

    # --- Üst: istatistik kartları -------------------------------------------
    stats_bar = theme.frame(win)
    stats_bar.pack(fill="x", padx=16, pady=(0, 8))
    series = records_db.measurement_series(state.session.patient_id, limit=100)
    if series:
        values = [s["kan_sekeri_degeri"] for s in series]
        stat_cards = [
            ("Son Ölçüm", f"{values[-1]:g} mg/dL"),
            ("Ortalama", f"{sum(values) / len(values):.1f} mg/dL"),
            ("Minimum", f"{min(values):g} mg/dL"),
            ("Maksimum", f"{max(values):g} mg/dL"),
            ("Ölçüm", f"{len(values)} adet"),
        ]
        for index, (title, value) in enumerate(stat_cards):
            cell = theme.frame(stats_bar, card=True)
            cell.grid(row=0, column=index, padx=6, pady=6, sticky="nsew")
            stats_bar.grid_columnconfigure(index, weight=1)
            theme.muted_label(cell, title, 9).pack(pady=(10, 0))
            theme.label(cell, value, 12, bold=True, fg=theme.PRIMARY).pack(pady=(0, 10))

    tip_filter_var = tk.StringVar(win, value="Tümü")
    filter_bar = theme.frame(win)
    filter_bar.pack(fill="x", padx=16, pady=(0, 6))
    theme.muted_label(filter_bar, "Ekranda göster:", 9).pack(side="left")
    tip_menu, _ = helpers.dropdown(filter_bar, ("Tümü", *MEAL_TIPS), width=12)
    tip_menu.pack(side="left", padx=8)

    table_card = theme.frame(win, card=True)
    table_card.pack(fill="both", expand=True, padx=16, pady=(0, 8))
    tree = ttk.Treeview(
        table_card,
        columns=("tarih", "saat", "tip", "deger", "gecerli", "not"),
        show="headings",
        height=8,
        style="Card.Treeview",
    )
    for key, text, width in (
        ("tarih", "Tarih", 100),
        ("saat", "Saat", 70),
        ("tip", "Ölçüm Tipi", 110),
        ("deger", "Kan Şekeri", 130),
        ("gecerli", "Ortalamaya Dahil", 130),
        ("not", "Not", 240),
    ):
        tree.heading(key, text=text)
        tree.column(key, width=width, anchor="w")
    tree.pack(side="left", fill="both", expand=True, padx=(1, 0), pady=1)
    vsb = ttk.Scrollbar(table_card, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=vsb.set)
    vsb.pack(side="right", fill="y")

    chart_box = theme.frame(win, card=True)
    chart_box.pack(fill="both", expand=True, padx=16, pady=(0, 12))

    def refresh() -> None:
        selected_tip = tip_filter_var.get()
        rows = records_db.recent_measurements(state.session.patient_id, limit=200)
        if selected_tip != "Tümü":
            rows = [r for r in rows if r["olcum_tipi"] == selected_tip]
        tree.delete(*tree.get_children())
        for m in rows:
            tree.insert(
                "",
                "end",
                values=(
                    helpers.date_label(m["olcum_tarihi"]),
                    m["olcum_saati"].strftime("%H:%M") if m["olcum_saati"] else "—",
                    m["olcum_tipi"],
                    f"{m['kan_sekeri_degeri']:g} mg/dL",
                    "Evet" if m["gecerli_olcum"] else "Hayır",
                    m["notlar"] or "—",
                ),
            )
        charts.plot_blood_sugar_trend(
            chart_box,
            [r for r in series if selected_tip == "Tümü" or r["olcum_tipi"] == selected_tip]
            or series,
            target_range=(profile.get("hedef_kan_sekeri_min", 70), profile.get("hedef_kan_sekeri_max", 110)),
        )

    tip_menu["menu"].delete(0, "end")
    for option in ("Tümü", *MEAL_TIPS):
        tip_menu["menu"].add_command(
            label=option, command=lambda opt=option: (tip_filter_var.set(opt), refresh())
        )
    tip_filter_var.set("Tümü")
    refresh()
