"""Zengin demo verisi üretici (GUI olmadan).

Kullanım::

    python scripts/generate_demo_data.py            # ~90 gün veri üret
    python scripts/generate_demo_data.py --reset    # diyabet_takip DB'sini silip yeniden üret

Sadece ``diyabet_takip`` veritabanına yazılır (varsayılan); başka DB'lere
dokunmaz.
"""

from __future__ import annotations

import argparse
import datetime
import random
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent.parent))

from diyabet_takip.db import bootstrap
from diyabet_takip.db import doctors as doctors_db
from diyabet_takip.db import reference as ref
from diyabet_takip.db.client import date_at, get_db_strict
from diyabet_takip.services import (
    alert_service,
    compliance_service,
    insulin_service,
    measurement_service,
    stats_service,
)

random.seed(42)

EXTRA_PATIENTS = [
    ("33333333333", "Ayşe", "Kaya", "ayse.kaya@ornek.com", "Tip 1", (90, 140), True),
    ("44444444444", "Fatih", "Çelik", "fatih.celik@ornek.com", "Tip 2", (85, 150), False),
    ("55555555555", "Zeynep", "Arslan", "zeynep.arslan@ornek.com", "Tip 2", (90, 150), True),
]

DOCTOR_NOTES = [
    ("Kontrol Değerleri", "HbA1c 3 ayda bir bakılacak. Hedef: %7 altı.", "Yüksek"),
    ("Nutrisyon Görüşmesi", "Diyetisyen randevusu için yönlendirme yapılacak.", "Orta"),
    ("Egzersiz Uyarısı", "Yoğun antrenmanlarda hipoglisemi riski; ölçüm ü atlamayın.", "Yüksek"),
]

MEAL_CENTERS = {
    "Sabah": (7, 30),
    "Öğle": (12, 30),
    "İkindi": (15, 45),
    "Akşam": (18, 45),
    "Gece": (22, 15),
}


def _meter_value(good_control: bool) -> float:
    if good_control:
        return round(random.uniform(68, 185), 1)
    lo, hi = random.choice([(50, 120), (130, 210), (200, 320)])
    return round(random.uniform(lo, hi), 1)


def _offset_minutes(hh: int, mm: int, spread: int = 15) -> tuple[int, int]:
    total = hh * 60 + mm + random.randint(-spread, spread)
    return divmod(total, 60)


def generate_measurements(hasta_id, days: int, good: bool) -> int:
    """``days`` gün geriye doğru ölçüm üretir; oluşturulan ölçüm sayısını döner."""
    db = get_db_strict()
    now = datetime.datetime.now()
    n = 0
    for offset in range(days, 0, -1):
        day = now.date() - datetime.timedelta(days=offset)
        tips = list(MEAL_CENTERS)
        random.shuffle(tips)
        for tip in tips[: random.choice((2, 3, 3, 4, 4, 5))]:
            hh, mm = _offset_minutes(*MEAL_CENTERS[tip])
            dt = now.replace(
                year=day.year, month=day.month, day=day.day, hour=hh, minute=mm,
                second=0, microsecond=0,
            )
            if dt > now:
                continue  # gelecekteki ölçüm üretmeyiz
            value = _meter_value(good)
            gecerli = measurement_service.is_on_time(dt, tip)
            if not gecerli and random.random() < 0.5:
                # saat dışı örnekler gerçekçi saatlerde kalsın
                dt = dt.replace(hour=random.choice((0, 3, 5, 10, 21)))
                gecerli = measurement_service.is_on_time(dt, tip)
            db[bootstrap.MEASUREMENTS].insert_one(
                {
                    "hasta_id": hasta_id,
                    "olcum_zamani": dt,
                    "kan_sekeri_degeri": value,
                    "olcum_tipi": tip,
                    "gecerli": gecerli,
                    "notlar": "",
                    "kayit_zamani": dt,
                }
            )
            n += 1
            if value < 70 or value > 200:
                alert_service.evaluate_measurement(hasta_id, value, day)
    return n


def generate_logs_and_scores(hasta_id, days: int, compliant: bool) -> None:
    db = get_db_strict()
    now = datetime.datetime.now()
    diet_chance = 0.9 if compliant else 0.45
    exercise_chance = 0.85 if compliant else 0.35
    for offset in range(days, 0, -1):
        day = now.date() - datetime.timedelta(days=offset)
        diyet = random.random() < diet_chance
        egzersiz = random.random() < exercise_chance
        db[bootstrap.DIET_LOGS].update_one(
            {"hasta_id": hasta_id, "takip_tarihi": date_at(day)},
            {"$set": {"diyet_uygulandimi": diyet, "notlar": "",
                      "kayit_zamani": datetime.datetime.combine(day, datetime.time(21, 0))}},
            upsert=True,
        )
        db[bootstrap.EXERCISE_LOGS].update_one(
            {"hasta_id": hasta_id, "takip_tarihi": date_at(day)},
            {"$set": {"egzersiz_yapildimi": egzersiz, "sure_dakika": random.choice((20, 30, 45)),
                      "notlar": "",
                      "kayit_zamani": datetime.datetime.combine(day, datetime.time(21, 30))}},
            upsert=True,
        )
        insulin_service.generate_for_day(hasta_id, day)
        compliance_service.compute_for(hasta_id, day)
        stats_service.compute_for(hasta_id, day)


def generate_plans_notes_appointments(doktor_id) -> None:
    db = get_db_strict()
    diyetler = ref.get_diet_types()
    egzersizler = ref.get_exercise_types()
    for index, (tc, _ad, _soyad, _eposta, _tip, _hedef, compliant) in enumerate(EXTRA_PATIENTS):
        hasta_id = ref.find_patient_id_by_tc(db, tc)
        if not hasta_id:
            continue
        doctors_db.assign_diet_plan(
            doktor_id, hasta_id, diyetler[index % len(diyetler)][0],
            datetime.date.today() - datetime.timedelta(days=45),
            datetime.date.today() + datetime.timedelta(days=60),
        )
        doctors_db.assign_exercise_plan(
            doktor_id, hasta_id, egzersizler[index % len(egzersizler)][0],
            datetime.date.today() - datetime.timedelta(days=45),
            None,
            3 if compliant else 2,
            30,
        )
        baslik, icerik, onem = DOCTOR_NOTES[index % len(DOCTOR_NOTES)]
        note_time = datetime.datetime.now() - datetime.timedelta(days=2)
        db[bootstrap.DOCTOR_NOTES].insert_one(
            {
                "doktor_id": doktor_id,
                "hasta_id": hasta_id,
                "not_basligi": baslik,
                "not_icerigi": icerik,
                "etiketler": [],
                "onem_seviyesi": onem,
                "gorunurluk": "Doktor ve Hasta",
                "olusturma_tarihi": note_time,
                "guncelleme_tarihi": note_time,
            }
        )
        for girilen_dakika, durum in ((10, "Tamamlandı"), (3, "Tamamlandı"), (-5, "Planlandı")):
            db[bootstrap.APPOINTMENTS].insert_one(
                {
                    "doktor_id": doktor_id,
                    "hasta_id": hasta_id,
                    "randevu_tarihi": date_at(
                        datetime.date.today() + datetime.timedelta(days=girilen_dakika)
                    ),
                    "randevu_saati": "10:00",
                    "sure_dakika": 30,
                    "durum": durum,
                    "not_metni": "Kontrol",
                    "olusturma_tarihi": datetime.datetime.now(),
                }
            )


def main() -> None:
    parser = argparse.ArgumentParser(description="Demo verisi üretici")
    parser.add_argument("--reset", action="store_true", help="diyabet_takip DB'sini silip yeniden kur")
    parser.add_argument("--days", type=int, default=90, help="kaç gün geriye veri (varsayılan 90)")
    args = parser.parse_args()

    db = get_db_strict()
    if args.reset:
        print("diyabet_takip veritabanı siliniyor...")
        db.client.drop_database("diyabet_takip")
        db = get_db_strict()

    bootstrap.ensure_schema(db)
    bootstrap.seed_if_empty(db)

    doktor_user = db[bootstrap.USERS].find_one({"tc_kimlik_no": "11111111111"})
    doktor_profile = db[bootstrap.DOCTOR_PROFILES].find_one({"user_id": doktor_user["_id"]})
    doktor_id = doktor_profile["_id"]

    for tc, ad, soyad, eposta, tip, (hedef_min, hedef_max), _compliant in EXTRA_PATIENTS:
        if not ref.find_patient_id_by_tc(db, tc):
            result = doctors_db.add_patient(
                doktor_id=doktor_id,
                tc_no=tc, ad=ad, soyad=soyad, eposta=eposta,
                plain_password="hasta123",
                dogum_tarihi=datetime.date(1992, 6, 12),
                cinsiyet="Kadın" if ad in ("Ayşe", "Zeynep") else "Erkek",
                diyabet_tipi=tip,
                tani_tarihi=datetime.date(2024, 8, 1),
                hedef_min=hedef_min, hedef_max=hedef_max,
            )
            if not result["ok"]:
                print(f"  ! hasta eklenemedi {tc}: {result['mesaj']}")

    generate_plans_notes_appointments(doktor_id)

    for profile in db[bootstrap.PATIENT_PROFILES].find({"doktor_id": doktor_id}):
        hasta_id = profile["_id"]
        hedef_min = profile.get("hedef_kan_sekeri_min", 70)
        good = hedef_min >= 85            # 44* hastası "zayıf kontrol" olsun
        compliant = hedef_min >= 90
        n = generate_measurements(hasta_id, args.days, good)
        generate_logs_and_scores(hasta_id, args.days, compliant)
        print(f"hasta {hasta_id}: {n} ölçüm + {args.days} gün diyet/egzersiz/skor")

    dashboard = doctors_db.doctor_dashboard(doktor_id)
    print("dashboard:", dashboard)
    print(
        "Bitti! Demo hesaplar: 11111111111/doktor123 (Doktor) · "
        "22222222222/hasta123 (Hasta) · 33333333333/hasta123, "
        "44444444444/hasta123, 55555555555/hasta123"
    )


if __name__ == "__main__":
    main()
