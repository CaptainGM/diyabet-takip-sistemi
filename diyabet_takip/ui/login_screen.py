"""Giriş ekranı — v1'in 400x250 gri penceresi yerine kartlı modern tasarım."""

from __future__ import annotations

import tkinter as tk
from collections.abc import Callable
from tkinter import messagebox

from .. import state, theme
from ..services import auth_service


def show_login_screen(on_authenticated: Callable[[], None]) -> None:
    """Giriş kartını gösterir; başarılı girişte ``on_authenticated`` çağrılır."""
    state.session.reset()
    window = state.session.window
    # pencereyi hazırla
    for widget in window.winfo_children():
        widget.destroy()
    window.title("Diyabet Takip Sistemi — Giriş")
    window.geometry("460x600")
    window.configure(bg=theme.APP_BG)

    outer = tk.Frame(window, bg=theme.APP_BG)
    outer.pack(expand=True, fill="both")

    # --- Marka bloğu ----------------------------------------------------------
    brand = theme.frame(outer)
    brand.pack(pady=(40, 10))
    tk.Label(brand, text="🩺", font=("Segoe UI Emoji", 34), bg=theme.APP_BG).pack()
    theme.title_label(brand, "Diyabet Takip Sistemi", 18).pack(pady=(4, 0))
    theme.muted_label(
        brand,
        "Hasta ve doktor için kan şekeri, diyet, egzersiz ve uyarı takibi",
        9,
    ).pack()

    # --- Giriş kartı (Card) ---------------------------------------------------
    card = theme.frame(outer, card=True)
    card.pack(pady=16, padx=48, fill="x")

    theme.label(card, "Giriş", 13, bold=True).pack(anchor="w", pady=(18, 10), padx=20)

    theme.label(card, "T.C. Kimlik No", 9, fg=theme.MUTED).pack(
        anchor="w", padx=20, pady=(4, 2)
    )
    tc_entry = theme.entry(card, width=26)
    tc_entry.pack(ipadx=0, ipady=4, padx=20, fill="x")
    tc_entry.focus_set()

    theme.label(card, "Şifre", 9, fg=theme.MUTED).pack(anchor="w", padx=20, pady=(10, 2))
    password_entry = theme.entry(card, width=26, show="•")
    password_entry.pack(ipadx=0, ipady=4, padx=20, fill="x")

    def do_login(event=None):
        nonlocal tc_entry
        result = auth_service.authenticate(
            tc_entry.get().strip(), password_entry.get().strip()
        )
        if result["ok"]:
            state.session.user_id = result["user_id"]
            state.session.user_ad = result["ad"]
            state.session.user_soyad = result["soyad"]
            state.session.user_role = result["rol"]
            state.session.patient_id = result.get("patient_id")
            state.session.doctor_id = result.get("doctor_id")
            messagebox.showinfo(
                "Giriş Başarılı",
                f"Hoş geldiniz, {state.session.full_name} ({result['rol']})!",
            )
            on_authenticated()
        else:
            messagebox.showerror("Giriş Başarısız", result["mesaj"])
            password_entry.delete(0, tk.END)
            password_entry.focus_set()

    login_button = theme.button(card, "Giriş Yap", do_login)
    login_button.pack(fill="x", padx=20, pady=(18, 20), ipady=6)

    # --- Demo kullanıcıları ---------------------------------------------------
    hint = theme.frame(outer, card=True)
    hint.pack(pady=6, padx=48, fill="x")
    theme.label(hint, "Demo kullanıcılar", 10, bold=True).pack(anchor="w", padx=14, pady=(10, 4))
    theme.muted_label(
        hint, "Doktor: 11111111111 / doktor123  ·  Hasta: 22222222222 / hasta123", 9
    ).pack(anchor="w", padx=14, pady=(0, 10))

    window.bind("<Return>", do_login)
