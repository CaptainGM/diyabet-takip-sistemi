"""Uyum skoru — v1 ``hasta_uyum_skoru_hesapla`` procs + event karşılığı.

Son 7 gün içinde:
- diyet uyumu  : kayıt günleri içinde uygulanan diyabet yüzdesi
- egzersiz uyum: kayıt günleri içinde yapılan egzersiz yüzdesi
- ölçüm uyumu  : geçerli ölçüm yapılan farklı gün sayısının 7'ye oranı
- genel skor   : 0.4*p + 0.3*e + 0.3*ö
"""

from __future__ import annotations

import datetime

from ..db import bootstrap as B
from ..db.client import date_at, get_db


def compute_for(hasta_id, day: datetime.date) -> dict | None:
    db = get_db()
    if db is None:
        return None
    start = date_at(day - datetime.timedelta(days=6))
    end = date_at(day + datetime.timedelta(days=1))

    diet_docs = list(
        db[B.DIET_LOGS].find(
            {"hasta_id": hasta_id, "takip_tarihi": {"$gte": start, "$lt": end}},
            {"diyet_uygulandimi": 1},
        )
    )
    diyet_uyum = (
        sum(1 for d in diet_docs if d.get("diyet_uygulandimi")) * 100.0 / len(diet_docs)
        if diet_docs
        else 0.0
    )

    ex_docs = list(
        db[B.EXERCISE_LOGS].find(
            {"hasta_id": hasta_id, "takip_tarihi": {"$gte": start, "$lt": end}},
            {"egzersiz_yapildimi": 1},
        )
    )
    egz_uyum = (
        sum(1 for d in ex_docs if d.get("egzersiz_yapildimi")) * 100.0 / len(ex_docs)
        if ex_docs
        else 0.0
    )

    olcum_gunleri = {
        m["olcum_zamani"].date()
        for m in db[B.MEASUREMENTS].find(
            {
                "hasta_id": hasta_id,
                "gecerli": True,
                "olcum_zamani": {"$gte": start, "$lt": end},
            },
            {"olcum_zamani": 1},
        )
    }
    olcum_uyum = len(olcum_gunleri) * 100.0 / 7

    genel = round(diyet_uyum * 0.4 + egz_uyum * 0.3 + olcum_uyum * 0.3, 2)
    doc = {
        "diyet_uyum_orani": round(diyet_uyum, 2),
        "egzersiz_uyum_orani": round(egz_uyum, 2),
        "olcum_uyum_orani": round(olcum_uyum, 2),
        "genel_uyum_skoru": genel,
        "hesaplama_tarihi": date_at(day),
    }
    db[B.COMPLIANCE_SCORES].update_one(
        {"hasta_id": hasta_id, "hesaplama_tarihi": date_at(day)},
        {"$set": doc},
        upsert=True,
    )
    return doc


def compute_for_all(day: datetime.date) -> int:
    db = get_db()
    if db is None:
        return 0
    n = 0
    for profile in db[B.PATIENT_PROFILES].find({}, {"_id": 1}):
        if compute_for(profile["_id"], day):
            n += 1
    return n
