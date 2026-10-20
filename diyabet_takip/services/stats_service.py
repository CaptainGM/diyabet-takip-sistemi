"""Günlük kan şekeri istatistikleri — v1 ``gunluk_istatistik_hesapla`` karşılığı."""

from __future__ import annotations

import datetime
import statistics

from ..db import bootstrap as B
from ..db.client import date_at, get_db
from ..db.reference import find_patient_profile


def compute_for(hasta_id, day: datetime.date) -> dict | None:
    db = get_db()
    if db is None:
        return None
    start = date_at(day)
    end = date_at(day + datetime.timedelta(days=1))
    docs = list(
        db[B.MEASUREMENTS].find(
            {
                "hasta_id": hasta_id,
                "gecerli": True,
                "olcum_zamani": {"$gte": start, "$lt": end},
            },
            {"kan_sekeri_degeri": 1},
        )
    )
    values = [float(d["kan_sekeri_degeri"]) for d in docs]
    if not values:
        return None

    profile = find_patient_profile(db, hasta_id) or {}
    hedef_min = profile.get("hedef_kan_sekeri_min", 70)
    hedef_max = profile.get("hedef_kan_sekeri_max", 110)
    in_target = sum(1 for v in values if hedef_min <= v <= hedef_max)

    doc = {
        "hasta_id": hasta_id,
        "istatistik_tarihi": date_at(day),
        "minimum_deger": round(min(values), 2),
        "maksimum_deger": round(max(values), 2),
        "ortalama_deger": round(statistics.mean(values), 2),
        "standart_sapma": round(statistics.stdev(values), 2) if len(values) > 1 else 0.0,
        "olcum_sayisi": len(values),
        "hedef_aralik_uyum_yuzdesi": round(in_target * 100.0 / len(values), 2),
    }
    db[B.BLOOD_SUGAR_STATS].update_one(
        {"hasta_id": hasta_id, "istatistik_tarihi": date_at(day)},
        {"$set": doc},
        upsert=True,
    )
    return doc


def compute_range(hasta_id, start_day: datetime.date, end_day: datetime.date) -> int:
    n = 0
    day = start_day
    while day <= end_day:
        if compute_for(hasta_id, day):
            n += 1
        day += datetime.timedelta(days=1)
    return n
