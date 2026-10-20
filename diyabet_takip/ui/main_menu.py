"""Ana menü — v1'in uzun buton listesi yerine tile-grid'i olan modern ekran."""

from __future__ import annotations

import tkinter as tk

from .. import state, theme
from . import navigation

DOCTOR_TILES = [
    ("📊", "Panelim / Durum Özeti"),
    ("👥", "Hastalarım ve Filtreleme"),
    ("➕", "Yeni Hasta Ekle"),
    ("🚨", "Hasta Uyarıları"),
    ("🩹", "Kritik Hastalar"),
    ("🧾", "Hasta Raporu Oluştur"),
    ("🗂️", "Hastaya Plan/Belirti Ata"),
    ("🗓️", "Randevu Yönetimi"),
    ("👤", "Profilim / Şifre"),
]

PATIENT_TILES = [
    ("🩸", "Kan Şekeri Ölçümü Gir"),
    ("🥗", "Diyet/Egzersiz Durumu Gir"),
    ("🤕", "Semptom Takibi Yap"),
    ("📈", "Kan Şekeri Geçmişi ve Grafikler"),
    ("🎯", "Diyet/Egzersiz Uyum Takibi (%)"),
    ("💉", "İnsülin Önerilerim (Filtreli)"),
    ("🔔", "Bildirimlerim"),
    ("📋", "Doktorumun Planları ve Notları"),
    ("🗓️", "Randevularım"),
    ("👤", "Profilim / Şifre"),
]


def show_main_app_screen() -> None:
    window = state.session.window
    if window is None:
        return
    for widget in window.winfo_children():
        widget.destroy()
    window.title(f"Diyabet Takip Sistemi — {state.session.user_role}")
    window.geometry("1080x760")
    window.configure(bg=theme.APP_BG)
    window.resizable(True, True)

    # --- Üst bar -------------------------------------------------------------
    topbar = theme.frame(window, card=True)
    topbar.pack(fill="x")
    theme.title_label(topbar, " 🩺 Diyabet Takip Sistemi", 13).pack(
        side="left", padx=18, pady=12
    )
    right = theme.frame(topbar, card=True)
    right.pack(side="right", padx=12, pady=8)
    theme.button(
        right,
        f"{state.session.full_name} · {state.session.user_role}",
        None,
        style="ghost",
    ).pack(side="left", padx=(0, 8))
    theme.button(right, "Çıkış Yap", navigation.go_login, style="danger").pack(side="left")

    # --- Tile grid (kaydırılabilir) ------------------------------------------
    canvas = tk.Canvas(window, bg=theme.APP_BG, highlightthickness=0)
    scrollbar = tk.Scrollbar(window, orient="vertical", command=canvas.yview)
    scroll_frame = theme.frame(canvas, card=False)
    scroll_frame.bind(
        "<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
    )
    canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)

    tiles = DOCTOR_TILES if state.session.user_role == "Doktor" else PATIENT_TILES
    grid = theme.frame(scroll_frame)
    grid.pack(expand=True, fill="both", padx=40, pady=30)
    for index, (icon, text) in enumerate(tiles):
        tile = tk.Frame(
            grid,
            bg=theme.CARD_BG,
            highlightbackground=theme.BORDER,
            highlightthickness=1,
            cursor="hand2",
        )
        row, col = divmod(index, 3)
        tile.grid(row=row, column=col, padx=14, pady=14, ipadx=8, sticky="nsew")
        tile.bind("<Enter>", lambda e, t=tile: t.config(bg="#eff7f8"))
        tile.bind("<Leave>", lambda e, t=tile: t.config(bg=theme.CARD_BG))
        icon_label = tk.Label(
            tile, text=icon, font=("Segoe UI Emoji", 26), bg=theme.CARD_BG
        )
        icon_label.pack(pady=(22, 6))
        text_label = tk.Label(
            tile,
            text=text,
            font=theme.font(10, bold=True),
            bg=theme.CARD_BG,
            fg=theme.TEXT,
            wraplength=200,
            justify="center",
        )
        text_label.pack(padx=10, pady=(0, 22))
        for clickable in (tile, icon_label, text_label):
            clickable.bind("<Button-1>", lambda e, idx=index: _open_tile(idx))

    for col in range(3):
        grid.grid_columnconfigure(col, weight=1)

    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")


def _open_tile(index: int) -> None:
    """Tile index → ekran fonksiyonu (lazy import; döngü yok)."""
    from .doctor.alerts import show_critical_patients, show_doctor_alerts
    from .doctor.dashboard import show_doctor_dashboard
    from .doctor.patients import add_patient_screen, show_doctor_patients_with_filters
    from .doctor.plans import show_add_to_system_options
    from .doctor.reports import show_appointment_management, show_patient_report_options
    from .patient.appointments import show_appointments_screen
    from .patient.insulin import (
        show_insulin_recommendations_for_patient_filtered,
        show_patient_notifications,
    )
    from .patient.measurements import (
        enter_blood_sugar,
        show_blood_sugar_history_and_graphs,
    )
    from .patient.plans import show_doctor_plans_for_patient
    from .patient.tracking import (
        enter_diet_exercise,
        enter_symptoms,
        show_patient_compliance,
    )
    from .profile import show_profile_screen

    if state.session.user_role == "Doktor":
        actions = {
            0: show_doctor_dashboard,
            1: show_doctor_patients_with_filters,
            2: add_patient_screen,
            3: show_doctor_alerts,
            4: show_critical_patients,
            5: show_patient_report_options,
            6: show_add_to_system_options,
            7: show_appointment_management,
            8: show_profile_screen,
        }
    else:
        actions = {
            0: enter_blood_sugar,
            1: enter_diet_exercise,
            2: enter_symptoms,
            3: show_blood_sugar_history_and_graphs,
            4: show_patient_compliance,
            5: show_insulin_recommendations_for_patient_filtered,
            6: show_patient_notifications,
            7: show_doctor_plans_for_patient,
            8: show_appointments_screen,
            9: show_profile_screen,
        }
    actions[index]()
