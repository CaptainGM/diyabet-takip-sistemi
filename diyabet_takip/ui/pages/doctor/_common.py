"""Doktor sayfaları arasında paylaşılan sabitler ve küçük biçimlendiriciler."""

from __future__ import annotations

from ... import helpers

DIABET_TYPES = ("Tip 1", "Tip 2", "Gestasyonel", "Ön Diyabet")
IMPORTANCE = ("Düşük", "Orta", "Yüksek")
VISIBILITY = ("Doktor ve Hasta", "Sadece Doktor")


def _date(value) -> str:
    return helpers.date_label(value)


def _value_text(value, unit: str = "mg/dL") -> str:
    return "—" if value is None else f"{float(value):g} {unit}"
