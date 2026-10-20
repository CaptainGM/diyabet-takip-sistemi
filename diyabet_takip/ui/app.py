"""Uygulama giriş noktası: kök Tk penceresi + ekran döngüsü."""

from __future__ import annotations

import tkinter as tk

from .. import state, theme
from . import navigation
from .login_screen import show_login_screen
from .main_menu import show_main_app_screen


def launch() -> None:
    """Uygulamayı başlatır. ``python -m diyabet_takip`` tarafından çağrılır."""
    root = tk.Tk()
    state.session.window = root
    root.title("Diyabet Takip Sistemi")
    root.geometry("470x640+120+80")

    theme.apply_theme(root)

    navigation.register_main_screen(show_main_app_screen)
    navigation.register_login_screen(show_login_screen)

    show_login_screen(show_main_app_screen)

    root.mainloop()
