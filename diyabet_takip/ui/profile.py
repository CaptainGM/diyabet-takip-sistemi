"""Profilim — kullanıcı bilgileri + şifre değiştirme (v2'de eklenen özellik)."""

from __future__ import annotations

from tkinter import messagebox

from .. import state, theme
from ..services import auth_service
from . import helpers


def show_profile_screen() -> None:
    win = helpers.modal_window(None, "Profilim / Şifre", "520x560")
    helpers.header(win, "👤 Profilim", "Hesap bilgileriniz ve şifre değiştirme")

    db_ok = state.session.user_id is not None

    # --- Hesap bilgileri -------------------------------------------------------
    info_card = theme.frame(win, card=True)
    info_card.pack(fill="x", padx=18, pady=(0, 10))
    theme.label(info_card, "Hesap Bilgileri", 11, bold=True).pack(
        anchor="w", padx=14, pady=(10, 4)
    )
    rows = [
        ("Ad Soyad", state.session.full_name or "—"),
        ("Rol", state.session.user_role or "—"),
    ]
    for key, value in rows:
        line = theme.frame(info_card)
        line.pack(fill="x", padx=14, pady=2)
        theme.muted_label(line, key, 9, width=10).pack(side="left")
        theme.label(line, value, 10).pack(side="left", padx=(20, 0))

    tc_line = theme.frame(win, card=True)
    tc_line.pack(fill="x", padx=18, pady=(0, 10))
    theme.muted_label(tc_line, f"Oturum ID: {state.session.user_id}", 8).pack(
        anchor="w", padx=14, pady=6
    )

    # --- Şifre değiştirme -------------------------------------------------------
    pass_card = theme.frame(win, card=True)
    pass_card.pack(fill="x", padx=18, pady=(0, 10))
    form = theme.frame(pass_card)
    form.pack(padx=12, pady=12)

    mevcut_entry = theme.entry(form, show="•")
    helpers.form_row(form, 0, "Mevcut Şifre:", mevcut_entry)
    yeni_entry = theme.entry(form, show="•")
    helpers.form_row(form, 1, "Yeni Şifre (6-40 karakter):", yeni_entry)
    tekrar_entry = theme.entry(form, show="•")
    helpers.form_row(form, 2, "Yeni Şifre (Tekrar):", tekrar_entry)

    def change() -> None:
        if not db_ok:
            return
        yeni = yeni_entry.get()
        if yeni != tekrar_entry.get():
            messagebox.showerror("Hata", "Yeni şifreler eşleşmiyor.", parent=win)
            return
        result = auth_service.change_password(
            state.session.user_id, mevcut_entry.get(), yeni
        )
        if result["ok"]:
            messagebox.showinfo("Başarı", result["mesaj"], parent=win)
            win.destroy()
        else:
            messagebox.showerror("Hata", result["mesaj"], parent=win)

    theme.button(pass_card, "Şifreyi Güncelle", change, style="primary").pack(
        fill="x", padx=14, pady=(6, 14), ipady=4
    )
    theme.muted_label(
        pass_card,
        "Şifreler PBKDF2-HMAC-SHA256 ile hash'lenir; düz metin saklanmaz.",
        8,
    ).pack(anchor="w", padx=16, pady=(0, 10))
