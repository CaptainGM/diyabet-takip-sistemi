"""Referans verileri (belirti/diyet/egzersiz türleri, sistem ayarları)."""

from __future__ import annotations

import datetime

from pymongo.database import Database

from . import bootstrap as B
from .client import as_date, get_db


def get_symptom_options() -> list[tuple]:
    """[(belirti_id, belirti_adi), ...] — ekranlarda geçmelı seçim listeleri."""
    db = get_db()
    if db is None:
        return []
    docs = db[B.SYMPTOM_TYPES].find({}, {"belirti_adi": 1}).sort("belirti_adi", 1)
    return [(doc["_id"], doc["belirti_adi"]) for doc in docs]


def get_diet_types() -> list[tuple]:
    db = get_db()
    if db is None:
        return []
    docs = db[B.DIET_TYPES].find({}, {"diyet_adi": 1}).sort("diyet_adi", 1)
    return [(doc["_id"], doc["diyet_adi"]) for doc in docs]


def get_exercise_types() -> list[tuple]:
    db = get_db()
    if db is None:
        return []
    docs = db[B.EXERCISE_TYPES].find({}, {"egzersiz_adi": 1}).sort("egzersiz_adi", 1)
    return [(doc["_id"], doc["egzersiz_adi"]) for doc in docs]


def get_setting(db: Database, key:str, default=None):
    doc = db[B.SYSTEM_SETTINGS].find_one({"anahtar": key})
    return doc["deger"] if doc else default


def find_patient_profile(db: Database, hasta_id) -> dict | None:
    """Hasta profili + kullanıcı bilgisi (UI gösterimi için)."""
    pipeline = [
        {"$match": {"_id": hasta_id}},
        {
            "$lookup": {
                "from": B.USERS,
                "localField": "user_id",
                "foreignField": "_id",
                "as": "user",
            }
        },
        {"$unwind": "$user"},
    ]
    row = list(db[B.PATIENT_PROFILES].aggregate(pipeline))
    if not row:
        return None
    doc = row[0]
    user = doc["user"]
    return {
        "hasta_id": doc["_id"],
        "ad": user["ad"],
        "soyad": user["soyad"],
        "tc_kimlik_no": user.get("tc_kimlik_no"),
        "diyabet_tipi": doc.get("diyabet_tipi"),
        "hedef_kan_sekeri_min": doc.get("hedef_kan_sekeri_min", 70),
        "hedef_kan_sekeri_max": doc.get("hedef_kan_sekeri_max", 110),
        "tani_tarihi": as_date(doc.get("tani_tarihi")),
        "doktor_id": doc.get("doktor_id"),
        "user_id": user["_id"],
    }


def find_patient_id_by_tc(db: Database, tc_no: str):
    """TC no ile hasta _id (doktor plan atama ekranları)."""
    user = db[B.USERS].find_one({"tc_kimlik_no": tc_no, "rol": "Hasta"}, {"_id": 1})
    if not user:
        return None
    profile = db[B.PATIENT_PROFILES].find_one({"user_id": user["_id"]}, {"_id": 1})
    return profile["_id"] if profile else None


def find_doctor_profile_id(db: Database, user_id):
    profile = db[B.DOCTOR_PROFILES].find_one({"user_id": user_id}, {"_id": 1})
    return profile["_id"] if profile else None


def find_patient_profile_id(db: Database, user_id):
    profile = db[B.PATIENT_PROFILES].find_one({"user_id": user_id}, {"_id": 1})
    return profile["_id"] if profile else None


def _start_of_day(d: datetime.date) -> datetime.datetime:
    return datetime.datetime(d.year, d.month, d.day)
