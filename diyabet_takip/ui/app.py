"""Uygulama giriş noktası: kök Tk penceresi + ekran döngüsü."""

from __future__ import annotations

import ctypes
import pathlib
import sys
import tkinter as tk

from .. import state, theme
from . import navigation
from .login_screen import show_login_screen
from .main_menu import show_main_app_screen

ASSETS = pathlib.Path(__file__).resolve().parent.parent.parent / "assets"


def _enable_high_dpi() -> None:
    """Yüksek çözünürlüklü monitörlerde Tk metnini bulanıklaşmaktan kurtarır."""
    if sys.platform != "win32":
        return
    try:
        # Per-monitor DPI awareness: Windows pencereyi bitmap olarak büyütmez.
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
    except Exception:
        try:
            ctypes.windll.user32.SetProcessDPIAware()
        except Exception:
            pass


def apply_app_icon(root: tk.Tk) -> None:
    """Python logosu yerine uygulamanın kendi ikonu (assets/app.ico)."""
    ico = ASSETS / "app.ico"
    png = ASSETS / "app.png"
    try:
        if ico.exists():
            root.iconbitmap(default=str(ico))
        if png.exists():
            image = tk.PhotoImage(file=str(png))
            root.iconphoto(True, image)
            root._app_icon_image = image  # GC'ye karşı referans
    except tk.TclError:
        pass


def launch() -> None:
    """Uygulamayı başlatır. ``python -m diyabet_takip`` tarafından çağrılır."""
    _enable_high_dpi()
    # Windows görev çubuğunda python.exe yerine uygulama ikonu/grubu görünsün.
    try:
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
            "Sahin.DiyabetTakipSistemi"
        )
    except Exception:
        pass

    root = tk.Tk()
    state.session.window = root
    root.title("Diyabet Takip Sistemi")
    root.geometry("470x640+120+80")
    root.minsize(900, 640)

    theme.apply_theme(root)
    apply_app_icon(root)

    def toggle_fullscreen(_event=None):
        root.attributes("-fullscreen", not root.attributes("-fullscreen"))

    def quit_fullscreen(_event=None):
        root.attributes("-fullscreen", False)

    root.bind("<F11>", toggle_fullscreen)
    root.bind("<Escape>", quit_fullscreen)

    navigation.register_main_screen(show_main_app_screen)
    navigation.register_login_screen(show_login_screen)

    show_login_screen(show_main_app_screen)

    root.mainloop()
