"""Her iki rolün de kullandığı ortak sorgular.

Not: v1'de bu sorgular düz SQL string'leri yüreğiydi; v2'de MongoDB
aggregation pipeline'ları kullanılır ve UI'ın beklediği dict anahtarlarına
(örn. ``kan_sekeri_degeri``, ``olcum_tarihi``) dönüntü yapılmaya devam eder.
"""

from __future__ import annotations

import datetime

from . import bootstrap as B
from .client import as_date, as_time, date_at, get_db


def recent_measurements(hasta_id, limit: int = 50) -> list[dict]:
    db = get_db()
    if db is None:
        return []
    docs = (
        db[B.MEASUREMENTS]
        .find({"hasta_id": hasta_id})
        .sort([("olcum_zamani", -1)])
        .limit(limit)
    )
    return [
        {
            "olcum_id": doc["_id"],
            "olcum_tarihi": as_date(doc["olcum_zamani"]),
            "olcum_saati": as_time(doc["olcum_zamani"]),
            "olcum_zamani": doc["olcum_zamani"],
            "kan_sekeri_degeri": round(float(doc["kan_sekeri_degeri"]), 2),
            "olcum_tipi": doc.get("olcum_tipi"),
            "gecerli_olcum": doc.get("gecerli", True),
            "notlar": doc.get("notlar"),
        }
        for doc in docs
    ]


def measurement_series(hasta_id, limit: int = 100) -> list[dict]:
    """Kısa grafik verisi: sadece geçerli ölçümler, zaman sıralı.

    En YENİ ``limit`` ölçüm alınır ve kronolojik (artan) düzende döner.
    """
    db = get_db()
    if db is None:
        return []
    docs = (
        db[B.MEASUREMENTS]
        .find({"hasta_id": hasta_id, "gecerli": True}, {"olcum_zamani": 1, "kan_sekeri_degeri": 1})
        .sort("olcum_zamani", -1)
        .limit(limit)
    )
    rows = [
        {
            "olcum_zamani": doc["olcum_zamani"],
            "kan_sekeri_degeri": float(doc["kan_sekeri_degeri"]),
        }
        for doc in docs
    ]
    rows.reverse()
    return rows


def daily_average(hasta_id, d: datetime.date) -> float | None:
    db = get_db()
    if db is None:
        return None
    docs = db[B.MEASUREMENTS].aggregate(
        [
            {
                "$match": {
                    "hasta_id": hasta_id,
                    "gecerli": True,
                    "olcum_zamani": {
                        "$gte": date_at(d),
                        "$lt": date_at(d + datetime.timedelta(days=1)),
                    },
                }
            },
            {"$group": {"_id": None, "ortalama": {"$avg": "$kan_sekeri_degeri"}}},
        ]
    )
    row = next(iter(docs), None)
    return round(float(row["ortalama"]), 2) if row else None


def diet_exercise_history(hasta_id, limit: int = 30) -> list[dict]:
    """v1 LEFT JOIN davranışı: aynı tarihte diyet/egzersiz kayıtları birleşik."""
    db = get_db()
    if db is None:
        return []
    diets = {
        doc["takip_tarihi"]: doc
        for doc in (
            db[B.DIET_LOGS].find({"hasta_id": hasta_id}).sort("takip_tarihi", -1).limit(limit)
        )
    }
    exercises = {
        doc["takip_tarihi"]: doc
        for doc in (
            db[B.EXERCISE_LOGS].find({"hasta_id": hasta_id}).sort("takip_tarihi", -1).limit(limit)
        )
    }
    days = sorted(set(diets) | set(exercises), reverse=True)[:limit]
    out = []
    for d in days:
        diet = diets.get(d)
        ex = exercises.get(d)
        out.append(
            {
                "takip_tarihi": d,
                "diyet_uygulandimi": bool(diet.get("diyet_uygulandimi")) if diet else None,
                "egzersiz_yapildimi": bool(ex.get("egzersiz_yapildimi")) if ex else None,
                "sure_dakika": ex.get("sure_dakika") if ex else None,
            }
        )
    return out


def compliance_history(hasta_id, limit: int = 30) -> list[dict]:
    db = get_db()
    if db is None:
        return []
    docs = (
        db[B.COMPLIANCE_SCORES]
        .find({"hasta_id": hasta_id})
        .sort("hesaplama_tarihi", -1)
        .limit(limit)
    )
    return [
        {
            "hesaplama_tarihi": as_date(doc["hesaplama_tarihi"]),
            "diyet_uyum_orani": float(doc.get("diyet_uyum_orani", 0)),
            "egzersiz_uyum_orani": float(doc.get("egzersiz_uyum_orani", 0)),
            "olcum_uyum_orani": float(doc.get("olcum_uyum_orani", 0)),
            "genel_uyum_skoru": float(doc.get("genel_uyum_skoru", 0)),
        }
        for doc in docs
    ]


def symptom_history(hasta_id, limit: int = 50) -> list[dict]:
    db = get_db()
    if db is None:
        return []
    pipeline = [
        {"$match": {"hasta_id": hasta_id}},
        {"$sort": {"kayit_tarihi": -1, "kayit_zamani": -1}},
        {"$limit": limit},
        {
            "$lookup": {
                "from": B.SYMPTOM_TYPES,
                "localField": "belirti_id",
                "foreignField": "_id",
                "as": "type",
            }
        },
        {"$unwind": {"path": "$type", "preserveNullAndEmptyArrays": True}},
        {
            "$lookup": {
                "from": B.DOCTOR_PROFILES,
                "localField": "doktor_id",
                "foreignField": "_id",
                "as": "doctor",
            }
        },
        {"$unwind": {"path": "$doctor", "preserveNullAndEmptyArrays": True}},
        {
            "$lookup": {
                "from": B.USERS,
                "localField": "doctor.user_id",
                "foreignField": "_id",
                "as": "doctor_user",
            }
        },
        {"$unwind": {"path": "$doctor_user", "preserveNullAndEmptyArrays": True}},
    ]
    out = []
    for doc in db[B.SYMPTOM_RECORDS].aggregate(pipeline):
        name = doc.get("type", {}).get("belirti_adi") or "Bilinmeyen"
        if doc.get("kaydeden_role") == "Doktor" and doc.get("doctor_user"):
            recorder = f"{doc['doctor_user']['ad']} {doc['doctor_user']['soyad']}"
        else:
            recorder = "Hasta Kaydı"
        out.append(
            {
                "kayit_tarihi": as_date(doc["kayit_tarihi"]),
                "belirti_adi": name,
                "siddet_seviyesi": doc.get("siddet_seviyesi"),
                "notlar": doc.get("notlar"),
                "kaydeden": recorder,
            }
        )
    return out


def insulin_history(hasta_id, start: datetime.date | None = None, end: datetime.date | None = None, limit: int = 30) -> list[dict]:
    db = get_db()
    if db is None:
        return []
    q: dict = {"hasta_id": hasta_id}
    if start or end:
        rango = {}
        if start:
            rango["$gte"] = date_at(start)
        if end:
            rango["$lte"] = date_at(end)
        q["tarih"] = rango
    docs = (
        db[B.INSULIN_RECS]
        .find(q)
        .sort([("tarih", -1), ("olcum_tipi", 1)])
        .limit(limit)
    )
    return [
        {
            "oneri_id": doc["_id"],
            "tarih": as_date(doc["tarih"]),
            "olcum_tipi": doc["olcum_tipi"],
            "ortalama_kan_sekeri": round(float(doc["ortalama_kan_sekeri"]), 2),
            "onerilen_doz_ml": float(doc["onerilen_doz_ml"]),
            "uygulandi": bool(doc.get("uygulandi")),
        }
        for doc in docs
    ]


def active_diet_plan(hasta_id) -> dict | None:
    db = get_db()
    if db is None:
        return None
    today = date_at(datetime.date.today())
    doc = db[B.DIET_PLANS].find_one(
        {
            "hasta_id": hasta_id,
            "aktif_durum": True,
            "baslangic_tarihi": {"$lte": today},
            "$or": [{"bitis_tarihi": None}, {"bitis_tarihi": {"$gte": today}}],
        },
        sort=[("olusturma_tarihi", -1)],
    )
    if not doc:
        return None
    return {
        "diyet_adi": doc.get("diyet_adi"),
        "aciklama": doc.get("aciklama"),
        "baslangic_tarihi": as_date(doc["baslangic_tarihi"]),
        "bitis_tarihi": as_date(doc.get("bitis_tarihi")),
    }


def active_exercise_plan(hasta_id) -> dict | None:
    db = get_db()
    if db is None:
        return None
    today = date_at(datetime.date.today())
    doc = db[B.EXERCISE_PLANS].find_one(
        {
            "hasta_id": hasta_id,
            "aktif_durum": True,
            "baslangic_tarihi": {"$lte": today},
            "$or": [{"bitis_tarihi": None}, {"bitis_tarihi": {"$gte": today}}],
        },
        sort=[("olusturma_tarihi", -1)],
    )
    if not doc:
        return None
    return {
        "egzersiz_adi": doc.get("egzersiz_adi"),
        "aciklama": doc.get("aciklama"),
        "haftalik_siklik": doc.get("haftalik_siklik"),
        "sure_dakika": doc.get("sure_dakika"),
        "baslangic_tarihi": as_date(doc["baslangic_tarihi"]),
        "bitis_tarihi": as_date(doc.get("bitis_tarihi")),
    }


def doctor_symptom_records_for_patient(hasta_id, days: int = 7) -> list[dict]:
    """Hasta ekranı: doktorun son N gün girilen belirtileri."""
    db = get_db()
    if db is None:
        return []
    cutoff = datetime.date.today() - datetime.timedelta(days=days)
    pipeline = [
        {
            "$match": {
                "hasta_id": hasta_id,
                "doktor_id": {"$ne": None},
                "kayit_tarihi": {"$gte": date_at(cutoff)},
            }
        },
        {"$sort": {"kayit_tarihi": -1, "kayit_zamani": -1}},
        {
            "$lookup": {
                "from": B.SYMPTOM_TYPES,
                "localField": "belirti_id",
                "foreignField": "_id",
                "as": "type",
            }
        },
        {"$unwind": {"path": "$type", "preserveNullAndEmptyArrays": True}},
    ]
    return [
        {
            "kayit_tarihi": as_date(doc["kayit_tarihi"]),
            "belirti_adi": doc.get("type", {}).get("belirti_adi") or "Bilinmeyen",
            "siddet_seviyesi": doc.get("siddet_seviyesi"),
            "notlar": doc.get("notlar"),
        }
        for doc in db[B.SYMPTOM_RECORDS].aggregate(pipeline)
    ]


def shared_doctor_notes(hasta_id) -> list[dict]:
    db = get_db()
    if db is None:
        return []
    docs = (
        db[B.DOCTOR_NOTES]
        .find({"hasta_id": hasta_id, "gorunurluk": "Doktor ve Hasta"})
        .sort("olusturma_tarihi", -1)
    )
    return [
        {
            "not_basligi": doc["not_basligi"],
            "not_icerigi": doc["not_icerigi"],
            "olusturma_tarihi": as_date(doc["olusturma_tarihi"]),
            "zamani": doc.get("olusturma_tarihi"),
            "onem_seviyesi": doc.get("onem_seviyesi"),
        }
        for doc in docs
    ]
