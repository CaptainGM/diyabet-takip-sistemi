"""Hasta ekranlarının sorgu/yazma işlemleri."""

from __future__ import annotations

import datetime

from . import bootstrap as B
from .client import as_date, date_at, get_db

__all__ = [
    "appointments_for_patient",
    "mark_insulin_applied",
    "mark_notification_read",
    "notifications_for_user",
    "record_symptoms_by_patient",
    "upsert_diet_log",
    "upsert_exercise_log",
]


def upsert_diet_log(hasta_id, takip_tarihi: datetime.date, uygulandimi: bool, notlar: str = "") -> None:
    db = get_db()
    if db is None:
        return
    db[B.DIET_LOGS].update_one(
        {"hasta_id": hasta_id, "takip_tarihi": date_at(takip_tarihi)},
        {
            "$set": {
                "diyet_uygulandimi": uygulandimi,
                "notlar": notlar,
                "kayit_zamani": datetime.datetime.now(),
            }
        },
        upsert=True,
    )


def upsert_exercise_log(
    hasta_id, takip_tarihi: datetime.date, yapildimi: bool, sure_dakika: int | None, notlar: str = ""
) -> None:
    db = get_db()
    if db is None:
        return
    db[B.EXERCISE_LOGS].update_one(
        {"hasta_id": hasta_id, "takip_tarihi": date_at(takip_tarihi)},
        {
            "$set": {
                "egzersiz_yapildimi": yapildimi,
                "sure_dakika": sure_dakika,
                "notlar": notlar,
                "kayit_zamani": datetime.datetime.now(),
            }
        },
        upsert=True,
    )


def record_symptoms_by_patient(
    hasta_id, kayit_tarihi: datetime.date, siddet: str, notlar: str, belirti_ids: list
) -> int:
    db = get_db()
    if db is None:
        return 0
    saved = 0
    for belirti_id in belirti_ids:
        result = db[B.SYMPTOM_RECORDS].update_one(
            {
                "hasta_id": hasta_id,
                "belirti_id": belirti_id,
                "kayit_tarihi": date_at(kayit_tarihi),
            },
            {
                "$set": {
                    "siddet_seviyesi": siddet,
                    "notlar": notlar,
                    "doktor_id": None,
                    "kaydeden_role": "Hasta",
                    "kayit_zamani": datetime.datetime.now(),
                }
            },
            upsert=True,
        )
        saved += 1 if (result.upserted_id or result.modified_count > 0) else 0
    return saved


def mark_insulin_applied(oneri_id, hasta_id) -> bool:
    db = get_db()
    if db is None:
        return False
    res = db[B.INSULIN_RECS].update_one(
        {"_id": oneri_id, "hasta_id": hasta_id}, {"$set": {"uygulandi": True}}
    )
    return res.modified_count > 0


def notifications_for_user(kullanici_id, limit: int = 50) -> list[dict]:
    db = get_db()
    if db is None:
        return []
    docs = (
        db[B.NOTIFICATIONS]
        .find({"kullanici_id": kullanici_id})
        .sort("olusturma_tarihi", -1)
        .limit(limit)
    )
    return [
        {
            "bildirim_id": doc["_id"],
            "baslik": doc["baslik"],
            "mesaj": doc["mesaj"],
            "bildirim_tipi": doc.get("bildirim_tipi"),
            "okundu": bool(doc.get("okundu")),
            "olusturma_tarihi": as_date(doc["olusturma_tarihi"]),
            "zamani": doc.get("olusturma_tarihi"),
        }
        for doc in docs
    ]


def mark_notification_read(bildirim_id, kullanici_id) -> bool:
    db = get_db()
    if db is None:
        return False
    res = db[B.NOTIFICATIONS].update_one(
        {"_id": bildirim_id, "kullanici_id": kullanici_id},
        {"$set": {"okundu": True, "okunma_tarihi": datetime.datetime.now()}},
    )
    return res.modified_count > 0


def appointments_for_patient(hasta_id) -> list[dict]:
    db = get_db()
    if db is None:
        return []
    pipeline = [
        {"$match": {"hasta_id": hasta_id}},
        {"$sort": {"randevu_tarihi": -1}},
        {"$limit": 100},
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
    return [
        {
            "randevu_id": doc["_id"],
            "doktor_adi": (
                f"{doc.get('doctor_user', {}).get('ad', '')} "
                f"{doc.get('doctor_user', {}).get('soyad', '')}".strip() or "—"
            ),
            "uzmanlik": doc.get("doctor", {}).get("uzmanlik_alani"),
            "randevu_tarihi": as_date(doc["randevu_tarihi"]),
            "randevu_saati": doc.get("randevu_saati"),
            "sure_dakika": doc.get("sure_dakika"),
            "durum": doc.get("durum"),
            "not_metni": doc.get("not_metni"),
        }
        for doc in db[B.APPOINTMENTS].aggregate(pipeline)
    ]
