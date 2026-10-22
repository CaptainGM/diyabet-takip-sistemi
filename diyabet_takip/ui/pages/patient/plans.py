"""Hasta — doktorun atadığı planlar ve paylaşılan notlar."""

from __future__ import annotations

import tkinter as tk

from .... import state, theme
from ....db import records as records_db
from ... import icons
from ..base import Page, card, empty, section, table


class PatientPlansPage(Page):
    title = "Planlarım"
    subtitle = "Doktorunuzun atadığı diyet ve egzersiz planı ile paylaşılan notları görün."
    icon = "clipboard"
    accent = theme.PURPLE

    def build(self) -> None:
        self.page_head(
            actions=(theme.button(self, "Belirti Ekle", lambda: self.app.navigate("lifestyle", tab="symptom"), style="primary"),)
        )
        diet = records_db.active_diet_plan(state.session.patient_id)
        exercise = records_db.active_exercise_plan(state.session.patient_id)
        top = tk.Frame(self.body, bg=theme.APP_BG)
        top.pack(fill="x", pady=(0, 12))
        for idx, (title, value, sub, accent, icon_name) in enumerate((
            ("Diyet Planı", diet["diyet_adi"] if diet else "Plan yok",
             (diet or {}).get("aciklama") or "Doktorunuz henüz diyet planı atamadı.", theme.GREEN, "apple"),
            ("Egzersiz Planı", exercise["egzersiz_adi"] if exercise else "Plan yok",
             f"Haftada {exercise['haftalik_siklik']} kez · {exercise['sure_dakika']} dk"
             if exercise else "Doktorunuz henüz egzersiz planı atamadı.", theme.ORANGE, "dumbbell"),
        )):
            c = card(top, padx=16, pady=14, accent=accent)
            c.pack(side="left", fill="both", expand=True, padx=(0, 6) if idx == 0 else (6, 0))
            row = tk.Frame(c.body, bg=theme.CARD_BG)
            row.pack(fill="x")
            icons.badge(row, icon_name, accent, size=42, bg=theme.CARD_BG).pack(side="left", padx=(0, 12))
            text = tk.Frame(row, bg=theme.CARD_BG)
            text.pack(side="left", fill="x", expand=True)
            tk.Label(text, text=title, font=theme.font(8, True), bg=theme.CARD_BG, fg=theme.MUTED).pack(anchor="w")
            tk.Label(text, text=value, font=theme.font(13, True), bg=theme.CARD_BG, fg=theme.TEXT).pack(anchor="w")
            tk.Label(c.body, text=sub, font=theme.font(8), bg=theme.CARD_BG, fg=theme.MUTED,
                     anchor="w", wraplength=500, justify="left").pack(anchor="w", pady=(10, 0))

        bottom = tk.Frame(self.body, bg=theme.APP_BG)
        bottom.pack(fill="both", expand=True)
        left = card(bottom, padx=14, pady=12)
        left.pack(side="left", fill="both", expand=True, padx=(0, 6))
        section(left.body, "Doktor Notları", "Sizinle paylaşılan değerlendirmeler", icon="report", accent=theme.TEAL)
        notes = records_db.shared_doctor_notes(state.session.patient_id)
        if not notes:
            empty(left.body, "Henüz paylaşılmış doktor notu yok.", icon="report").pack(fill="both", expand=True)
        for note in notes[:4]:
            row = tk.Frame(left.body, bg=theme.CARD_2, highlightbackground=theme.BORDER, highlightthickness=1)
            row.pack(fill="x", pady=3)
            top_row = tk.Frame(row, bg=theme.CARD_2)
            top_row.pack(fill="x", padx=10, pady=(8, 2))
            tk.Label(top_row, text=note["not_basligi"], font=theme.font(9, True), bg=theme.CARD_2,
                     fg=theme.TEXT).pack(side="left")
            tk.Label(top_row, text=note["olusturma_tarihi"].strftime("%d.%m.%Y") if note.get("olusturma_tarihi") else "",
                     font=theme.font(8), bg=theme.CARD_2, fg=theme.MUTED).pack(side="right")
            tk.Label(row, text=note["not_icerigi"], font=theme.font(8), bg=theme.CARD_2, fg=theme.MUTED,
                     anchor="w", wraplength=680, justify="left").pack(fill="x", padx=10, pady=(0, 8))

        right = card(bottom, padx=0, pady=0)
        right.pack(side="left", fill="both", expand=True, padx=(6, 0))
        head = tk.Frame(right.body, bg=theme.CARD_BG)
        head.pack(fill="x", padx=14, pady=(12, 8))
        section(head, "Belirti Geçmişi", "Son 30 gün", icon="bandage", accent=theme.ORANGE)
        tree, wrap = table(
            right.body,
            ("tarih", "belirti", "siddet", "kaydeden", "not"),
            ("Tarih", "Belirti", "Şiddet", "Kaydeden", "Not"),
            (95, 150, 90, 130, 220), height=9,
        )
        wrap.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        for idx, row in enumerate(records_db.symptom_history(state.session.patient_id, limit=30)):
            tree.insert("", "end", tags=("odd" if idx % 2 else "even",), values=(
                row["kayit_tarihi"].strftime("%d.%m.%Y"), row["belirti_adi"],
                row["siddet_seviyesi"] or "—", row["kaydeden"], row["notlar"] or "—",
            ))

    def refresh(self) -> None:
        self.app.navigate("patient_plans")
