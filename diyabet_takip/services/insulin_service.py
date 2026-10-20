"""İnsülin doz önerisi — v1 ``insulin_onerisi_olustur`` procs karşılığı.

Kümülatif öğün ortalaması mantığı aynen korunur: 'Gece' önerisi için o
günün tüm geçerli ölçümleri, 'İkindi' için Sabah+Öğle+İkindi vs.
"""

from __future__ import annotations

import datetime

from ..db import bootstrap as B
from ..db.client import date_at, get_db

VALID_TIPS = ["Sabah", "Öğle", "İkindi", "Akşam", "Gece"]
# v1'deki ``ogun_ortalama_kan_sekeri_hesapla`` fonksiyonundaki kümülatif setler
CUMULATIVE_TIPS = {
    "Sabah": ["Sabah"],
    "Öğle": ["Sabah", "Öğle"],
    "İkindi": ["Sabah", "Öğle", "İkindi"],
    "Akşam": ["Sabah", "Öğle", "İkindi", "Akşam"],
    "Gece": ["Sabah", "Öğle", "İkindi", "Akşam", "Gece"],
}


def meal_average(hasta_id, day: datetime.date, tip: str) -> float | None:
    """Kümülatif öğün ortalaması (yalnızca saat-dışı geçerli ölçümlere dahil)."""
    db = get_db()
    if db is None:
        return None
    start = date_at(day)
    end = date_at(day + datetime.timedelta(days=1))
    docs = db[B.MEASUREMENTS].aggregate(
        [
            {
                "$match": {
                    "hasta_id": hasta_id,
                    "gecerli": True,
                    "olcum_tipi": {"$in": CUMULATIVE_TIPS.get(tip, [tip])},
                    "olcum_zamani": {"$gte": start, "$lt": end},
                }
            },
            {"$group": {"_id": None, "avg": {"$avg": "$kan_sekeri_degeri"}}},
        ]
    )
    row = next(iter(docs), None)
    return float(row["avg"]) if row else None


def dose_for(avg: float) -> float:
    """v1 ``insulin_doz_hesapla`` fonksiyonu."""
    if avg > 200:
        return 3.0
    if avg >= 151:
        return 2.0
    if avg >= 111:
        return 1.0
    return 0.0


def update_recommendation(hasta_id, day: datetime.date, tip: str) -> bool:
    """O gün/öğün için öneri upsert eder. Öneri yoksa dokunmaz."""
    if tip not in VALID_TIPS:
        return False
    db = get_db()
    if db is None:
        return False
    avg = meal_average(hasta_id, day, tip)
    if avg is None or avg <= 0:
        return False
    db[B.INSULIN_RECS].update_one(
        {"hasta_id": hasta_id, "tarih": date_at(day), "olcum_tipi": tip},
        {
            "$set": {
                "ortalama_kan_sekeri": round(avg, 2),
                "onerilen_doz_ml": dose_for(avg),
                "olusturma_tarihi": datetime.datetime.now(),
            }
        },
        upsert=True,
    )
    return True


def generate_for_day(hasta_id, day: datetime.date) -> int:
    """Belirli günün tüm öğünleri için öneri üretir (batch)."""
    created = 0
    for tip in VALID_TIPS:
        if update_recommendation(hasta_id, day, tip):
            created += 1
    return created
