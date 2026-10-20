"""Hasta — doktorun atadığı planlar, notlar ve belirti kayıtları görünümü."""

from __future__ import annotations

import tkinter as tk  # noqa: F401  (görsel widget'lar için gerekli olabilir)
from tkinter import ttk

from ... import state, theme
from ...db import records as records_db
from .. import helpers


def show_doctor_plans_for_patient() -> None:
    win = helpers.modal_window(None, "Doktorumun Planları ve Notları", "840x720")
    helpers.header(
        win, "📋 Doktorumun Planları, Belirti Notlarım ve Doktor Notlarım"
    )

    windows = theme.frame(win)
    windows.pack(fill="both", expand=True, padx=16, pady=(0, 12))
    windows.grid_columnconfigure((0, 1), weight=1)

    # --- Aktif planlar ---------------------------------------------------------
    diet_plan = records_db.active_diet_plan(state.session.patient_id)
    ex_plan = records_db.active_exercise_plan(state.session.patient_id)

    diet_card = theme.frame(windows, card=True)
    diet_card.grid(row=0, column=0, padx=(0, 8), pady=(0, 10), sticky="nsew")

    theme.label(diet_card, "🥗 Aktif Diyet Planı", 11, bold=True).pack(
        anchor="w", padx=14, pady=(10, 4)
    )
    if diet_plan:
        theme.label(diet_card, diet_plan["diyet_adi"], 12, bold=True, fg=theme.PRIMARY).pack(
            anchor="w", padx=14, pady=2
        )
        theme.muted_label(
            diet_card,
            f"{helpers.date_label(diet_plan['baslangic_tarihi'])} → "
            f"{helpers.date_label(diet_plan['bitis_tarihi'])}",
            9,
        ).pack(anchor="w", padx=14)
        theme.label(diet_card, diet_plan["aciklama"] or "—", 9).pack(
            anchor="w", padx=14, pady=(2, 10)
        )
    else:
        theme.muted_label(diet_card, "Aktif diyet planı bulunmuyor.", 9).pack(
            anchor="w", padx=14, pady=(0, 10)
        )

    ex_card = theme.frame(windows, card=True)
    ex_card.grid(row=0, column=1, padx=(8, 0), pady=(0, 10), sticky="nsew")
    theme.label(ex_card, "🏃 Aktif Egzersiz Planı", 11, bold=True).pack(
        anchor="w", padx=14, pady=(10, 4)
    )
    if ex_plan:
        theme.label(ex_card, ex_plan["egzersiz_adi"], 12, bold=True, fg=theme.PRIMARY).pack(
            anchor="w", padx=14, pady=2
        )
        theme.muted_label(
            ex_card,
            f"Haftada {ex_plan['haftalik_siklik']} kez / {ex_plan['sure_dakika']} dk · "
            f"{helpers.date_label(ex_plan['baslangic_tarihi'])} → "
            f"{helpers.date_label(ex_plan['bitis_tarihi'])}",
            9,
        ).pack(anchor="w", padx=14, pady=(2, 10))
        theme.label(ex_card, ex_plan["aciklama"] or "—", 9).pack(
            anchor="w", padx=14, pady=(2, 10)
        )
    else:
        theme.muted_label(ex_card, "Aktif egzersiz planı bulunmuyor.", 9).pack(
            anchor="w", padx=14, pady=(0, 10)
        )

    # --- Doktor belirti kayıtları -------------------------------------------
    sym_card = theme.frame(windows, card=True)
    sym_card.grid(row=1, column=0, columnspan=2, sticky="nsew", padx=(0, 0), pady=(0, 10))
    theme.label(
        sym_card, "🩺 Doktorunuzun Son 7 Günde Girdiği Belirtiler", 11, bold=True
    ).pack(anchor="w", padx=14, pady=(10, 4))
    sym_rows = records_db.doctor_symptom_records_for_patient(state.session.patient_id, days=7)
    if not sym_rows:
        theme.muted_label(sym_card, "Doktor kaydı yok.", 9).pack(anchor="w", padx=14, pady=(0, 10))
    else:
        sym_tree = ttk.Treeview(
            sym_card, columns=("tarih", "belirti", "siddet", "not"), show="headings", height=5
        )
        for key, text, width in (
            ("tarih", "Tarih", 100),
            ("belirti", "Belirti", 180),
            ("siddet", "Şiddet", 90),
            ("not", "Not", 280),
        ):
            sym_tree.heading(key, text=text)
            sym_tree.column(key, width=width, anchor="w")
        sym_tree.pack(fill="both", expand=True, padx=14, pady=(0, 10))
        for row in sym_rows:
            sym_tree.insert(
                "",
                "end",
                values=(
                    helpers.date_label(row["kayit_tarihi"]),
                    row["belirti_adi"],
                    row["siddet_seviyesi"] or "—",
                    row["notlar"] or "—",
                ),
            )

    # --- Doktor notları --------------------------------------------------------
    notes_card = theme.frame(windows, card=True)
    notes_card.grid(row=2, column=0, columnspan=2, sticky="nsew")
    theme.label(notes_card, "📝 Doktor Notları (Görünür)", 11, bold=True).pack(
        anchor="w", padx=14, pady=(10, 4)
    )
    notes = records_db.shared_doctor_notes(state.session.patient_id)
    if not notes:
        theme.muted_label(notes_card, "Paylaşılmış doktor notu bulunmuyor.", 9).pack(
            anchor="w", padx=14, pady=(0, 10)
        )
    for note in notes:
        one_note = theme.frame(notes_card)
        one_note.pack(fill="x", padx=14, pady=4)
        theme.label(
            one_note,
            f"• {note['not_basligi']}  ({note['onem_seviyesi']} · "
            f"{helpers.date_label(note['olusturma_tarihi'])})",
            10, bold=True,
        ).pack(anchor="w")
        theme.label(one_note, note["not_icerigi"], 9).pack(anchor="w", padx=(14, 0), pady=(0, 4))
