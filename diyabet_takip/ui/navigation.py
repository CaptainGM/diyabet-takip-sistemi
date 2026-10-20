"""Ekranlar arası dolaşım (import döngülerini kırmak için ara katman).

app.py başlangıçta iki ekranın fonksiyonlarını kayıt eder; tüm ekranlar
bunları çağırır ama birbirini import etmez.
"""

from __future__ import annotations

from collections.abc import Callable

_to_main: Callable[[], None] | None = None
_to_login: Callable[[], None] | None = None


def register_main_screen(fn: Callable[[], None]) -> None:
    global _to_main
    _to_main = fn


def register_login_screen(fn: Callable[[], None]) -> None:
    global _to_login
    _to_login = fn


def go_main() -> None:
    if _to_main:
        _to_main()


def go_login() -> None:
    if _to_login:
        _to_login()
