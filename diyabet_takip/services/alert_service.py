"""Uyarı servisi — v1 trigger'ı ``kan_sekeri_uyari_kontrol`` karşılığı.

Eşikler ``system_settings`` koleksiyonundan okunur; kurallar:

- < hipoglisemi eşiği            → Acil Uyarı (Kritik)
- > hiperglisemi eşiği           → Acil Müdahale Uyarısı (Kritik)
- 151-200 mg/dL                  → İzleme Uyarısı (Yüksek)
- 111-150 mg/dL                  → Takip Uyarısı (Orta)

Saat dışı ölçümlerde uyarı yerine hastaya bildirim gider.
"""

from __future__ import annotations

import datetime

from ..db import bootstrap as B
from ..db.client import date_at, get_db
from ..db.reference import get_setting


def db_active_patient_doc(hasta_id) -> dict | None:
    from ..db.client import get_db

    db = get_db()
    if db is None:
        return None
    return db[B.PATIENT_PROFILES].find_one({"_id": hasta_id})


def create_alert(
    hasta_id, doktor_id, uyari_adi: str, mesaj: str, kayit_tarihi: datetime.date, deger: float | None = None
) -> None:
    db = get_db()
    if db is None:
        return
    t = db[B.ALERT_TYPES].find_one({"uyari_adi": uyari_adi})
    if not t:
        return
    now = datetime.datetime.now()
    db[B.ALERTS].insert_one(
        {
            "hasta_id": hasta_id,
            "doktor_id": doktor_id,
            "uyari_turu_id": t["_id"],
            "uyari_adi": uyari_adi,
            "aciliyet_seviyesi": t.get("aciliyet_seviyesi"),
            "uyari_mesaji": mesaj,
            "kan_sekeri_degeri": deger,
            "uyari_tarihi": date_at(kayit_tarihi),
            "okundu": False,
            "olusturma_tarihi": now,
        }
    )


def evaluate_measurement(hasta_id, value: float, kayit_tarihi: datetime.date) -> str | None:
    """Geçerli ölçüm için uyarı değerlendirmesi; uyarı adı ya da None döner."""
    db = get_db()
    if db is None:
        return None
    hypo = float(get_setting(db, "hipoglisemi_esik", 70))
    hyper = float(get_setting(db, "hiperglisemi_esik", 200))
    profile = db_active_patient_doc(hasta_id) or {}
    doktor_id = profile.get("doktor_id")

    uyari_adi = None
    if value < hypo:
        uyari_adi = "Acil Uyarı"
        mesaj = (
            f"Hastanın kan şekeri seviyesi {value:g} mg/dL ile kritik seviyenin "
            "altına düştü. Hipoglisemi riski! Hızlı müdahale gerekebilir."
        )
    elif value > hyper:
        uyari_adi = "Acil Müdahale Uyarısı"
        mesaj = (
            f"Hastanın kan şekeri {value:g} mg/dL ile kritik seviyenin üzerinde. "
            "Hiperglisemi durumu. Acil müdahale gerekebilir."
        )
    elif 151 <= value <= 200:
        uyari_adi = "İzleme Uyarısı"
        mesaj = (
            f"Hastanın kan şekeri {value:g} mg/dL. Diyabet kontrolü gereklidir."
        )
    elif 111 <= value <= 150:
        uyari_adi = "Takip Uyarısı"
        mesaj = f"Hastanın kan şekeri {value:g} mg/dL. Durum izlenmeli."

    if uyari_adi:
        create_alert(hasta_id, doktor_id, uyari_adi, mesaj, kayit_tarihi, value)
    return uyari_adi


def notify_out_of_window(hasta_id, value: float, dt: datetime.datetime) -> None:
    """Saat dışı ölçümde hastaya bildirim (v1 trigger ``bildirimler`` dalı)."""
    db = get_db()
    if db is None:
        return
    profile = db_active_patient_doc(hasta_id) or {}
    user_id = profile.get("user_id")
    if user_id is None:
        return
    db[B.NOTIFICATIONS].insert_one(
        {
            "kullanici_id": user_id,
            "baslik": "Ölçüm Zamanı Uyarısı",
            "mesaj": (
                f"Girdiğiniz kan şekeri ölçümü ({value:g} mg/dL) belirtilen saat "
                f"aralığının dışındadır ({dt.strftime('%d.%m.%Y %H:%M')}). "
                "Bu ölçüm ortalamaya dahil edilmeyecektir."
            ),
            "bildirim_tipi": "Uyarı",
            "okundu": False,
            "okunma_tarihi": None,
            "olusturma_tarihi": datetime.datetime.now(),
        }
    )


def check_daily_measurement_count(day: datetime.date, until_time: datetime.datetime | None = None) -> int:
    """Gün sonu kontrolü: ölçüm eksik/yetersiz uyarıları (event karşılığı)."""
    db = get_db()
    if db is None:
        return 0
    min_olcum = int(get_setting(db, "minimum_gunluk_olcum", 3))
    start = date_at(day)
    end = date_at(day + datetime.timedelta(days=1))
    q_time = f"{day.strftime('%d.%m.%Y')}"
    hasta_list = list(db[B.PATIENT_PROFILES].find({}))
    count = 0
    for profile in hasta_list:
        hasta_id = profile["_id"]
        valid_count = db[B.MEASUREMENTS].count_documents(
            {
                "hasta_id": hasta_id,
                "gecerli": True,
                "olcum_zamani": {"$gte": start, "$lt": end},
            }
        )
        if valid_count == 0:
            create_alert(
                hasta_id,
                profile.get("doktor_id"),
                "Ölçüm Eksik Uyarısı",
                "Hasta gün boyunca kan şekeri ölçümü yapmamıştır. Acil takip önerilir.",
                day,
            )
            count += 1
        elif valid_count < min_olcum:
            create_alert(
                hasta_id,
                profile.get("doktor_id"),
                "Ölçüm Yetersiz Uyarısı",
                f"Hastanın {q_time} tarihli ölçüm sayısı yetersiz ({valid_count}). Durum izlenmelidir.",
                day,
            )
            count += 1
    return count
