"""Kural tabanlı öneri — v1 ``kural_tabanli_oneri_getir`` procs karşılığı."""

from __future__ import annotations

from ..db import bootstrap as B
from ..db.client import get_db


def recommend(value: float, symptoms: list[str]) -> dict | None:
    """Kan şekeri + belirti seti en yakın kuralın önerisini döner."""
    db = get_db()
    if db is None:
        return None
    rules = list(db[B.RULE_BASE].find({"aktif_durum": True}))
    matching = [
        r for r in rules
        if (r.get("kan_sekeri_min") or 0) <= value <= (r.get("kan_sekeri_max") or 0)
        and set(r.get("belirtiler", [])) & set(symptoms)
    ]
    if not matching:
        return None

    def center(r):
        return ((r.get("kan_sekeri_min") or 0) + (r.get("kan_sekeri_max") or 0)) / 2

    best = min(matching, key=lambda r: abs(value - center(r)))
    return best
