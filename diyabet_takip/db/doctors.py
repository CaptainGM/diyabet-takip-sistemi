"""Doktor ekranlarının sorguları ve yazma işlemleri."""

from __future__ import annotations

import datetime

from .. import security
from . import bootstrap as B

# --- Hastalar -------------------------------------------------------------
from .client import as_date, date_at, get_db
from .reference import find_patient_id_by_tc, get_setting

__all__ = [
    "add_patient",
    "appointments_for_doctor",
    "assign_diet_plan",
    "assign_exercise_plan",
    "assign_symptoms",
    "average_glucose_for_doctor",
    "cancel_appointment",
    "create_appointment",
    "critical_patients_for_doctor",
    "doctor_dashboard",
    "doctor_notes_list",
    "glucose_distribution_for_doctor",
    "glucose_trend_for_doctor",
    "list_patients_for_doctor",
    "mark_alert_read",
    "measurement_counts_for_doctor",
    "patient_alerts_for_doctor",
    "recent_measurements_for_doctor",
    "save_doctor_note",
    "search_patients_for_doctor",
]


def list_patients_for_doctor(doktor_id) -> list[dict]:
    db = get_db()
    if db is None:
        return []
    out = []
    for doc in db[B.PATIENT_PROFILES].find({"doktor_id": doktor_id}):
        user = db[B.USERS].find_one({"_id": doc["user_id"]})
        if not user or not user.get("aktif_durum", True):
            continue
        out.append(
            {
                "hasta_id": doc["_id"],
                "ad": user["ad"],
                "soyad": user["soyad"],
                "tc_kimlik_no": user.get("tc_kimlik_no"),
                "diyabet_tipi": doc.get("diyabet_tipi"),
                "tani_tarihi": as_date(doc.get("tani_tarihi")),
            }
        )
    out.sort(key=lambda x: (x["ad"] or "", x["soyad"] or ""))
    return out


def search_patients_for_doctor(
    doktor_id,
    name_filter: str = "",
    min_bs: float | None = None,
    max_bs: float | None = None,
    symptom_id=None,
) -> list[dict]:
    """Hasta listesi + filtreleme (ad/tc, son kan şekeri, belirti)."""
    db = get_db()
    if db is None:
        return []
    base = list_patients_for_doctor(doktor_id)
    f = name_filter.strip().lower()
    out = []
    for p in base:
        full = f"{p['ad']} {p['soyad']}".lower()
        tc = (p.get("tc_kimlik_no") or "").lower()
        if f and f not in full and f not in tc:
            continue

        last = db[B.MEASUREMENTS].find_one(
            {"hasta_id": p["hasta_id"]},
            {"kan_sekeri_degeri": 1},
            sort=[("olcum_zamani", -1)],
        )
        p["son_kan_sekeri"] = round(float(last["kan_sekeri_degeri"]), 2) if last else None

        if min_bs is not None and (p["son_kan_sekeri"] is None or p["son_kan_sekeri"] < min_bs):
            continue
        if max_bs is not None and (p["son_kan_sekeri"] is None or p["son_kan_sekeri"] > max_bs):
            continue

        if symptom_id is not None:
            found = db[B.SYMPTOM_RECORDS].find_one(
                {"hasta_id": p["hasta_id"], "belirti_id": symptom_id},
                sort=[("kayit_tarihi", -1)],
            )
            if not found:
                continue

        p["son_belirtiler"] = _latest_symptom_names(db, p["hasta_id"])
        out.append(p)
    return out


def _latest_symptom_names(db, hasta_id) -> str | None:
    last = db[B.SYMPTOM_RECORDS].find_one(
        {"hasta_id": hasta_id}, {"kayit_tarihi": 1}, sort=[("kayit_tarihi", -1)]
    )
    if not last:
        return None
    names = []
    for rec in db[B.SYMPTOM_RECORDS].find(
        {"hasta_id": hasta_id, "kayit_tarihi": last["kayit_tarihi"]},
        {"belirti_id": 1},
    ):
        t = db[B.SYMPTOM_TYPES].find_one({"_id": rec["belirti_id"]}, {"belirti_adi": 1})
        if t:
            names.append(t["belirti_adi"])
    return ", ".join(names) if names else None


# --- Uyarılar -------------------------------------------------------------
def patient_alerts_for_doctor(doktor_id, limit: int = 100) -> list[dict]:
    db = get_db()
    if db is None:
        return []
    pipeline = [
        {"$match": {"doktor_id": doktor_id}},
        {"$sort": {"uyari_tarihi": -1, "olusturma_tarihi": -1}},
        {"$limit": limit},
        {
            "$lookup": {
                "from": B.PATIENT_PROFILES,
                "localField": "hasta_id",
                "foreignField": "_id",
                "as": "patient",
            }
        },
        {"$unwind": "$patient"},
        {
            "$lookup": {
                "from": B.USERS,
                "localField": "patient.user_id",
                "foreignField": "_id",
                "as": "user",
            }
        },
        {"$unwind": "$user"},
    ]
    out = [
        {
            "uyari_id": doc["_id"],
            "hasta_id": doc.get("hasta_id"),
            "hasta_adi": f"{doc['user'].get('ad', '')} {doc['user'].get('soyad', '')}".strip(),
            "hasta_tc": doc["user"].get("tc_kimlik_no"),
            "uyari_adi": doc.get("uyari_adi"),
            "aciliyet_seviyesi": doc.get("aciliyet_seviyesi"),
            "uyari_mesaji": doc.get("uyari_mesaji"),
            "uyari_tarihi": as_date(doc.get("uyari_tarihi")),
            "kan_sekeri_degeri": doc.get("kan_sekeri_degeri"),
            "okundu": bool(doc.get("okundu")),
        }
        for doc in db[B.ALERTS].aggregate(pipeline)
    ]
    priority = {"Kritik": 0, "Yüksek": 1, "Orta": 2, "Düşük": 3}
    # Önce en yeni uyarılar; sonra okunmamış + aciliyet önceliği (kararlı sıralama).
    out.sort(key=lambda a: a["uyari_tarihi"], reverse=True)
    out.sort(key=lambda a: (a["okundu"], priority.get(a["aciliyet_seviyesi"], 9)))
    return out[:limit]


def mark_alert_read(uyari_id) -> bool:
    db = get_db()
    if db is None:
        return False
    res = db[B.ALERTS].update_one({"_id": uyari_id}, {"$set": {"okundu": True}})
    return res.modified_count > 0


def critical_patients_for_doctor(doktor_id) -> list[dict]:
    """v1'deki ``kritik_hastalar`` VIEW'ünün aggregation karşılığı."""
    db = get_db()
    if db is None:
        return []
    hypo = float(get_setting(db, "hipoglisemi_esik", 70))
    hyper = float(get_setting(db, "hiperglisemi_esik", 200))
    min_olcum = int(get_setting(db, "minimum_gunluk_olcum", 3))
    cutoff = date_at(datetime.date.today() - datetime.timedelta(days=7))

    out = []
    for patient in db[B.PATIENT_PROFILES].find({"doktor_id": doktor_id}):
        user = db[B.USERS].find_one({"_id": patient["user_id"]})
        if not user or not user.get("aktif_durum", True):
            continue
        hasta_id = patient["_id"]
        meas = list(
            db[B.MEASUREMENTS].find(
                {"hasta_id": hasta_id, "olcum_zamani": {"$gte": cutoff}, "gecerli": True},
                {"kan_sekeri_degeri": 1, "olcum_zamani": 1},
            )
        )
        values = [float(m["kan_sekeri_degeri"]) for m in meas]
        gun_sayisi = len({m["olcum_zamani"].date() for m in meas})
        avg = sum(values) / len(values) if values else 0.0

        kritik_uyari = db[B.ALERTS].count_documents(
            {
                "hasta_id": hasta_id,
                "aciliyet_seviyesi": "Kritik",
                "uyari_tarihi": {"$gte": cutoff},
            }
        )
        score_row = db[B.COMPLIANCE_SCORES].find_one(
            {"hasta_id": hasta_id}, {"genel_uyum_skoru": 1}, sort=[("hesaplama_tarihi", -1)]
        )
        skor = float(score_row["genel_uyum_skoru"]) if score_row else 0.0

        kategori = "Stabil"
        if values and (avg < hypo or avg > hyper):
            kategori = "Kritik Durum (Kan Şekeri)"
        elif gun_sayisi < min_olcum:
            kategori = "Ölçüm Eksikliği"
        elif skor < 50:
            kategori = "Düşük Uyum"
        elif kritik_uyari > 0:
            kategori = "Kritik Uyarı Var"

        if kategori != "Stabil" or kritik_uyari > 0:
            out.append(
                {
                    "hasta_id": hasta_id,
                    "hasta_adi": f"{user['ad']} {user['soyad']}",
                    "son_7_gun_ortalama_kan_sekeri": avg,
                    "son_7_gun_olcum_gun_sayisi": gun_sayisi,
                    "kritik_uyari_sayisi": kritik_uyari,
                    "son_uyum_skoru": skor,
                    "durum_kategorisi": kategori,
                }
            )

    order = {
        "Kritik Durum (Kan Şekeri)": 0,
        "Ölçüm Eksikliği": 1,
        "Düşük Uyum": 2,
        "Kritik Uyarı Var": 3,
        "Stabil": 4,
    }
    out.sort(
        key=lambda x: (order.get(x["durum_kategorisi"], 4), -x["son_7_gun_ortalama_kan_sekeri"])
    )
    return out


def doctor_dashboard(doktor_id) -> dict:
    """v1'deki doktor_dashboard VIEW'ünün karşılığı (v2'de ayrı ekran)."""
    db = get_db()
    if db is None:
        return {}
    today = datetime.date.today()
    today_mid = date_at(today)
    tomorrow_mid = date_at(today + datetime.timedelta(days=1))
    week_ago = date_at(today - datetime.timedelta(days=7))
    toplam = db[B.PATIENT_PROFILES].count_documents({"doktor_id": doktor_id})

    hastalar = list(db[B.PATIENT_PROFILES].find({"doktor_id": doktor_id}, {"_id": 1}))
    hasta_ids = [h["_id"] for h in hastalar]
    bugun_olcum_yapan = len(
        {
            m["hasta_id"]
            for m in db[B.MEASUREMENTS].find(
                {
                    "hasta_id": {"$in": hasta_ids},
                    "olcum_zamani": {"$gte": today_mid, "$lt": tomorrow_mid},
                },
                {"hasta_id": 1},
            )
        }
    )
    okunmamis = db[B.ALERTS].count_documents({"doktor_id": doktor_id, "okundu": False})
    bugun_uyari = db[B.ALERTS].count_documents(
        {"doktor_id": doktor_id, "uyari_tarihi": {"$gte": today_mid, "$lt": tomorrow_mid}}
    )
    ort_skor = 0.0
    scores = list(
        db[B.COMPLIANCE_SCORES].aggregate(
            [
                {"$match": {"hasta_id": {"$in": hasta_ids}}},
                {"$match": {"hesaplama_tarihi": {"$gte": week_ago}}},
                {"$group": {"_id": None, "ort": {"$avg": "$genel_uyum_skoru"}}},
            ]
        )
    )
    if scores and scores[0].get("ort") is not None:
        ort_skor = round(float(scores[0]["ort"]), 1)
    return {
        "toplam_hasta_sayisi": toplam,
        "bugun_olcum_yapan_hasta_sayisi": bugun_olcum_yapan,
        "okunmamis_uyari_sayisi": okunmamis,
        "bugun_uyari_sayisi": bugun_uyari,
        "ortalama_hasta_uyum_skoru": ort_skor,
    }


# --- Dashboard verileri ---------------------------------------------------
def _doctor_patient_ids(db, doktor_id) -> list:
    return [
        row["_id"]
        for row in db[B.PATIENT_PROFILES].find({"doktor_id": doktor_id}, {"_id": 1})
    ]


def recent_measurements_for_doctor(doktor_id, limit: int = 6) -> list[dict]:
    """Doktorun hastalarından en yeni ölçümler (dashboard listesi)."""
    db = get_db()
    if db is None:
        return []
    ids = _doctor_patient_ids(db, doktor_id)
    if not ids:
        return []
    out = []
    docs = (
        db[B.MEASUREMENTS]
        .find({"hasta_id": {"$in": ids}, "gecerli": True})
        .sort([("olcum_zamani", -1)])
        .limit(limit)
    )
    for doc in docs:
        profile = db[B.PATIENT_PROFILES].find_one({"_id": doc["hasta_id"]}, {"user_id": 1})
        user = db[B.USERS].find_one({"_id": profile["user_id"]}) if profile else None
        name = f"{user['ad']} {user['soyad']}" if user else "Hasta"
        out.append(
            {
                "hasta_id": doc["hasta_id"],
                "hasta_adi": name,
                "kan_sekeri_degeri": round(float(doc["kan_sekeri_degeri"]), 1),
                "olcum_zamani": doc["olcum_zamani"],
                "olcum_tipi": doc.get("olcum_tipi"),
            }
        )
    return out


def glucose_trend_for_doctor(doktor_id, days: int = 7) -> list[dict]:
    """Doktorun tüm hastalarının günlük ortalama kan şekeri trendi."""
    db = get_db()
    if db is None:
        return []
    ids = _doctor_patient_ids(db, doktor_id)
    today = datetime.date.today()
    start = today - datetime.timedelta(days=max(days - 1, 0))
    if not ids:
        return [{"tarih": start + datetime.timedelta(days=i), "ortalama": None} for i in range(days)]
    rows = db[B.MEASUREMENTS].aggregate(
        [
            {
                "$match": {
                    "hasta_id": {"$in": ids},
                    "gecerli": True,
                    "olcum_zamani": {"$gte": date_at(start)},
                }
            },
            {
                "$group": {
                    "_id": {
                        "$dateToString": {"format": "%Y-%m-%d", "date": "$olcum_zamani"}
                    },
                    "ortalama": {"$avg": "$kan_sekeri_degeri"},
                }
            },
            {"$sort": {"_id": 1}},
        ]
    )
    by_day = {row["_id"]: round(float(row["ortalama"]), 1) for row in rows}
    return [
        {
            "tarih": start + datetime.timedelta(days=i),
            "ortalama": by_day.get((start + datetime.timedelta(days=i)).isoformat()),
        }
        for i in range(days)
    ]


def measurement_counts_for_doctor(doktor_id, days: int = 7) -> list[int]:
    """Son N günün günlük ölçüm sayıları (stat kartı sparkline)."""
    db = get_db()
    today = datetime.date.today()
    start = today - datetime.timedelta(days=max(days - 1, 0))
    counts = [0] * days
    if db is None:
        return counts
    ids = _doctor_patient_ids(db, doktor_id)
    if not ids:
        return counts
    rows = db[B.MEASUREMENTS].aggregate(
        [
            {
                "$match": {
                    "hasta_id": {"$in": ids},
                    "gecerli": True,
                    "olcum_zamani": {"$gte": date_at(start)},
                }
            },
            {
                "$group": {
                    "_id": {
                        "$dateToString": {"format": "%Y-%m-%d", "date": "$olcum_zamani"}
                    },
                    "adet": {"$sum": 1},
                }
            },
        ]
    )
    by_day = {row["_id"]: int(row["adet"]) for row in rows}
    for i in range(days):
        counts[i] = by_day.get((start + datetime.timedelta(days=i)).isoformat(), 0)
    return counts


def average_glucose_for_doctor(doktor_id, days: int = 7) -> float | None:
    """Son N günün tüm hastalar için ortalama kan şekeri."""
    trend = glucose_trend_for_doctor(doktor_id, days=days)
    values = [row["ortalama"] for row in trend if row["ortalama"] is not None]
    if not values:
        return None
    return round(sum(values) / len(values), 1)


def glucose_distribution_for_doctor(doktor_id, days: int = 30) -> dict:
    """Normal / yüksek / düşük ölçüm dağılımı (dashboard donut)."""
    db = get_db()
    if db is None:
        return {"normal": 0, "yuksek": 0, "dusuk": 0}
    ids = _doctor_patient_ids(db, doktor_id)
    if not ids:
        return {"normal": 0, "yuksek": 0, "dusuk": 0}
    start = date_at(datetime.date.today() - datetime.timedelta(days=max(days - 1, 0)))
    counts = {"normal": 0, "yuksek": 0, "dusuk": 0}
    cursor = db[B.MEASUREMENTS].find(
        {
            "hasta_id": {"$in": ids},
            "gecerli": True,
            "olcum_zamani": {"$gte": start},
        },
        {"kan_sekeri_degeri": 1},
    )
    for doc in cursor:
        value = float(doc["kan_sekeri_degeri"])
        if value < 70:
            counts["dusuk"] += 1
        elif value <= 140:
            counts["normal"] += 1
        else:
            counts["yuksek"] += 1
    return counts


# --- Doktor notları -------------------------------------------------------
def doctor_notes_list(doktor_id, hasta_id) -> list[dict]:
    db = get_db()
    if db is None:
        return []
    docs = (
        db[B.DOCTOR_NOTES]
        .find({"doktor_id": doktor_id, "hasta_id": hasta_id})
        .sort("olusturma_tarihi", -1)
    )
    return [
        {
            "not_basligi": doc["not_basligi"],
            "not_icerigi": doc["not_icerigi"],
            "olusturma_tarihi": as_date(doc["olusturma_tarihi"]),
            "zamani": doc.get("olusturma_tarihi"),
            "onem_seviyesi": doc.get("onem_seviyesi"),
            "gorunurluk": doc.get("gorunurluk"),
        }
        for doc in docs
    ]


def save_doctor_note(
    doktor_id, hasta_id, baslik: str, icerik: str, onem: str, gorunurluk: str
) -> None:
    db = get_db()
    if db is None:
        return
    now = datetime.datetime.now()
    db[B.DOCTOR_NOTES].insert_one(
        {
            "doktor_id": doktor_id,
            "hasta_id": hasta_id,
            "not_basligi": baslik,
            "not_icerigi": icerik,
            "etiketler": [],
            "onem_seviyesi": onem,
            "gorunurluk": gorunurluk,
            "olusturma_tarihi": now,
            "guncelleme_tarihi": now,
        }
    )


# --- Plan/belirti atama ---------------------------------------------------
def assign_symptoms(
    doktor_id, hasta_id, kayit_tarihi: datetime.date, siddet: str, notlar: str, belirti_ids: list
) -> int:
    """Belirti kaydı upsert (v1'deki ON DUPLICATE KEY UPDATE karşılığı)."""
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
                    "doktor_id": doktor_id,
                    "kaydeden_role": "Doktor",
                    "kayit_zamani": datetime.datetime.now(),
                }
            },
            upsert=True,
        )
        saved += 1 if (result.upserted_id or result.modified_count > 0) else 0
    return saved


def assign_diet_plan(
    doktor_id, hasta_id, diyet_turu_id, baslangic: datetime.date, bitis: datetime.date | None
) -> bool:
    db = get_db()
    if db is None:
        return False
    dt = db[B.DIET_TYPES].find_one({"_id": diyet_turu_id})
    bas_dt = date_at(baslangic)
    bit_dt = date_at(bitis) if bitis else None
    db[B.DIET_PLANS].update_many(
        {
            "hasta_id": hasta_id,
            "aktif_durum": True,
            "$or": [{"bitis_tarihi": None}, {"bitis_tarihi": {"$gte": bas_dt}}],
        },
        {"$set": {"aktif_durum": False, "bitis_tarihi": bas_dt - datetime.timedelta(days=1)}},
    )
    db[B.DIET_PLANS].insert_one(
        {
            "hasta_id": hasta_id,
            "doktor_id": doktor_id,
            "diyet_turu_id": diyet_turu_id,
            "diyet_adi": dt["diyet_adi"] if dt else None,
            "aciklama": (dt or {}).get("aciklama"),
            "baslangic_tarihi": bas_dt,
            "bitis_tarihi": bit_dt,
            "aktif_durum": True,
            "olusturma_tarihi": datetime.datetime.now(),
        }
    )
    return True


def assign_exercise_plan(
    doktor_id,
    hasta_id,
    egzersiz_turu_id,
    baslangic: datetime.date,
    bitis: datetime.date | None,
    haftalik_siklik: int,
    sure_dakika: int,
) -> bool:
    db = get_db()
    if db is None:
        return False
    et = db[B.EXERCISE_TYPES].find_one({"_id": egzersiz_turu_id})
    bas_dt = date_at(baslangic)
    bit_dt = date_at(bitis) if bitis else None
    db[B.EXERCISE_PLANS].update_many(
        {
            "hasta_id": hasta_id,
            "aktif_durum": True,
            "$or": [{"bitis_tarihi": None}, {"bitis_tarihi": {"$gte": bas_dt}}],
        },
        {"$set": {"aktif_durum": False, "bitis_tarihi": bas_dt - datetime.timedelta(days=1)}},
    )
    db[B.EXERCISE_PLANS].insert_one(
        {
            "hasta_id": hasta_id,
            "doktor_id": doktor_id,
            "egzersiz_turu_id": egzersiz_turu_id,
            "egzersiz_adi": et["egzersiz_adi"] if et else None,
            "aciklama": (et or {}).get("aciklama"),
            "baslangic_tarihi": bas_dt,
            "bitis_tarihi": bit_dt,
            "haftalik_siklik": haftalik_siklik,
            "sure_dakika": sure_dakika,
            "aktif_durum": True,
            "olusturma_tarihi": datetime.datetime.now(),
        }
    )
    return True


# --- Hasta ekleme ---------------------------------------------------------
def add_patient(
    doktor_id,
    tc_no: str,
    ad: str,
    soyad: str,
    eposta: str,
    plain_password: str,
    dogum_tarihi: datetime.date,
    cinsiyet: str,
    diyabet_tipi: str,
    tani_tarihi: datetime.date,
    hedef_min: int,
    hedef_max: int,
) -> dict:
    """Hasta + kullanıcı kaydı. Dönen dict: {ok: bool, mesaj: str}."""
    db = get_db()
    if db is None:
        return {"ok": False, "mesaj": "İşlem şu anda tamamlanamıyor. Lütfen tekrar deneyin."}

    if db[B.USERS].find_one(
        {"$or": [{"tc_kimlik_no": tc_no}, {"eposta": eposta}]}, {"_id": 1}
    ):
        return {"ok": False, "mesaj": "Bu T.C. Kimlik No veya e-posta ile zaten bir kullanıcı mevcut."}

    now = datetime.datetime.now()
    user_id = db[B.USERS].insert_one(
        {
            "tc_kimlik_no": tc_no,
            "ad": ad,
            "soyad": soyad,
            "dogum_tarihi": date_at(dogum_tarihi),
            "cinsiyet": cinsiyet,
            "eposta": eposta,
            "sifre_hash": security.hash_password(plain_password),
            "rol": "Hasta",
            "aktif_durum": True,
            "kayit_tarihi": now,
            "son_giris_tarihi": None,
        }
    ).inserted_id
    db[B.PATIENT_PROFILES].insert_one(
        {
            "user_id": user_id,
            "doktor_id": doktor_id,
            "tani_tarihi": date_at(tani_tarihi),
            "diyabet_tipi": diyabet_tipi,
            "hedef_kan_sekeri_min": hedef_min,
            "hedef_kan_sekeri_max": hedef_max,
            "notlar": "",
        }
    )
    return {"ok": True, "mesaj": f"{ad} {soyad} adlı hasta başarıyla eklendi!"}


# --- Randevular (v2'de eklenen yeni özellik) ------------------------------
def create_appointment(
    doktor_id, patient_select: str, randevu_tarihi: datetime.date, randevu_saati: str, sure: int, not_metni: str
) -> dict:
    """``patient_select`` = TC no. Hasta bulunamazsa hata döner."""
    db = get_db()
    if db is None:
        return {"ok": False, "mesaj": "İşlem şu anda tamamlanamıyor. Lütfen tekrar deneyin."}
    hasta_id = find_patient_id_by_tc(db, patient_select)
    if not hasta_id:
        return {"ok": False, "mesaj": "Bu T.C. Kimlik No ile hasta bulunamadı."}
    db[B.APPOINTMENTS].insert_one(
        {
            "doktor_id": doktor_id,
            "hasta_id": hasta_id,
            "randevu_tarihi": date_at(randevu_tarihi),
            "randevu_saati": randevu_saati,
            "sure_dakika": sure,
            "durum": "Planlandı",
            "not_metni": not_metni,
            "olusturma_tarihi": datetime.datetime.now(),
        }
    )
    return {"ok": True, "mesaj": "Randevu kaydedildi."}


def appointments_for_doctor(doktor_id, only_upcoming: bool = False) -> list[dict]:
    db = get_db()
    if db is None:
        return []
    q: dict = {"doktor_id": doktor_id}
    if only_upcoming:
        q["randevu_tarihi"] = {"$gte": date_at(datetime.date.today())}
    pipeline = [
        {"$match": q},
        {"$sort": {"randevu_tarihi": -1, "randevu_saati": 1}},
        {"$limit": 200},
        {
            "$lookup": {
                "from": B.PATIENT_PROFILES,
                "localField": "hasta_id",
                "foreignField": "_id",
                "as": "patient",
            }
        },
        {"$unwind": "$patient"},
        {
            "$lookup": {
                "from": B.USERS,
                "localField": "patient.user_id",
                "foreignField": "_id",
                "as": "user",
            }
        },
        {"$unwind": "$user"},
    ]
    return [
        {
            "randevu_id": doc["_id"],
            "hasta_adi": f"{doc['user']['ad']} {doc['user']['soyad']}",
            "hasta_tc": doc["user"].get("tc_kimlik_no"),
            "randevu_tarihi": as_date(doc["randevu_tarihi"]),
            "randevu_saati": doc.get("randevu_saati"),
            "sure_dakika": doc.get("sure_dakika"),
            "durum": doc.get("durum"),
            "not_metni": doc.get("not_metni"),
        }
        for doc in db[B.APPOINTMENTS].aggregate(pipeline)
    ]


def cancel_appointment(randevu_id) -> bool:
    db = get_db()
    if db is None:
        return False
    res = db[B.APPOINTMENTS].update_one(
        {"_id": randevu_id}, {"$set": {"durum": "İptal Edildi"}}
    )
    return res.modified_count > 0
