"""Hasta raporu — v1 ``hasta_rapor_olustur`` procs karşılığı.

Bölüme göre JSON benzeri dict veri döner; UI (aynı v1 ekranı) formatlar.
"""

from __future__ import annotations

import datetime

from ..db import bootstrap as B
from ..db.client import date_at, get_db
from ..db.reference import find_patient_profile


def build_report(hasta_id, start: datetime.date, end: datetime.date) -> list[dict]:
    db = get_db()
    if db is None:
        return []
    start_dt = date_at(start)
    end_dt = date_at(end + datetime.timedelta(days=1))
    sections: list[dict] = []

    profile = find_patient_profile(db, hasta_id)
    if profile:
        doctor = None
        if profile.get("doktor_id"):
            dprof = db[B.DOCTOR_PROFILES].find_one({"_id": profile["doktor_id"]})
            if dprof:
                doctor = db[B.USERS].find_one({"_id": dprof["user_id"]})
        sections.append(
            {
                "bolum": "Genel Bilgiler",
                "veri": {
                    "hasta_adi": f"{profile['ad']} {profile['soyad']}",
                    "tc_kimlik": profile.get("tc_kimlik_no"),
                    "diyabet_tipi": profile.get("diyabet_tipi"),
                    "tani_tarihi": profile.get("tani_tarihi").isoformat() if profile.get("tani_tarihi") else None,
                    "doktor_adi": (
                        f"{doctor['ad']} {doctor['soyad']}" if doctor else None
                    ),
                    "rapor_araligi": {"baslangic": start.isoformat(), "bitis": end.isoformat()},
                },
            }
        )

    # Kan şekeri istatistikleri
    meas = list(
        db[B.MEASUREMENTS].find(
            {
                "hasta_id": hasta_id,
                "gecerli": True,
                "olcum_zamani": {"$gte": start_dt, "$lt": end_dt},
            },
            {"kan_sekeri_degeri": 1},
        )
    )
    if meas:
        values = [float(m["kan_sekeri_degeri"]) for m in meas]
        in_range = sum(1 for v in values if 70 <= v <= 110)
        sections.append(
            {
                "bolum": "Kan Şekeri İstatistikleri",
                "veri": {
                    "ortalama": round(sum(values) / len(values), 2),
                    "minimum": round(min(values), 2),
                    "maksimum": round(max(values), 2),
                    "olcum_sayisi": len(values),
                    "normal_aralik_uyum": round(in_range * 100.0 / len(values), 2),
                },
            }
        )

    scores = list(
        db[B.COMPLIANCE_SCORES].aggregate(
            [
                {
                    "$match": {
                        "hasta_id": hasta_id,
                        "hesaplama_tarihi": {"$gte": start_dt, "$lt": end_dt},
                    }
                },
                {
                    "$group": {
                        "_id": None,
                        "ortalama_diyet_uyum": {"$avg": "$diyet_uyum_orani"},
                        "ortalama_egzersiz_uyum": {"$avg": "$egzersiz_uyum_orani"},
                        "ortalama_olcum_uyum": {"$avg": "$olcum_uyum_orani"},
                        "genel_uyum_skoru": {"$avg": "$genel_uyum_skoru"},
                    }
                },
            ]
        )
    )
    if scores:
        s = scores[0]
        sections.append(
            {
                "bolum": "Uyum Skorları",
                "veri": {
                    "ortalama_diyet_uyum": round(float(s["ortalama_diyet_uyum"] or 0), 2),
                    "ortalama_egzersiz_uyum": round(float(s["ortalama_egzersiz_uyum"] or 0), 2),
                    "ortalama_olcum_uyum": round(float(s["ortalama_olcum_uyum"] or 0), 2),
                    "genel_uyum_skoru": round(float(s["genel_uyum_skoru"] or 0), 2),
                },
            }
        )

    alert_ids = {
        d["_id"]: d["uyari_adi"] for d in db[B.ALERT_TYPES].find({}, {"uyari_adi": 1})
    }
    alerts = list(
        db[B.ALERTS].find(
            {
                "hasta_id": hasta_id,
                "uyari_tarihi": {"$gte": start_dt, "$lt": end_dt},
            },
            {"uyari_turu_id": 1},
        )
    )
    if alerts:
        def cnt(name: str) -> int:
            tid = next((k for k, v in alert_ids.items() if v == name), None)
            return sum(1 for a in alerts if a["uyari_turu_id"] == tid)

        sections.append(
            {
                "bolum": "Uyarı İstatistikleri",
                "veri": {
                    "toplam_uyari": len(alerts),
                    "acil_uyari": cnt("Acil Uyarı"),
                    "hiperglisemi_uyari": cnt("Acil Müdahale Uyarısı"),
                    "olcum_eksik_uyari": cnt("Ölçüm Eksik Uyarısı"),
                },
            }
        )

    return sections
