"""Hasta sayfaları arasında paylaşılan sabitler ve küçük biçimlendiriciler."""

from __future__ import annotations

MEAL_TIPS = ("Sabah", "Öğle", "İkindi", "Akşam", "Gece")
MEAL_TIPS_ALL = ("Tümü", *MEAL_TIPS)


def _num(value, unit: str = "mg/dL") -> str:
    return "—" if value is None else f"{float(value):g} {unit}"


def _yes(value) -> str:
    if value is None:
        return "Kayıt yok"
    return "Evet" if value else "Hayır"
