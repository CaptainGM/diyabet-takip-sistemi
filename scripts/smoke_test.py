r"""Uçtan uca duman testi (GUI olmadan).

Kullanım::

    python scripts\smoke_test.py

MongoDB'ye bağlanır; şemayı kurar, demo kullanıcıları üretir, servis ve
sorgu katmanını davranışsal olarak çalıştırır. Çıkış kodu 0 ise her şey OK.
"""

from __future__ import annotations

import datetime
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent.parent))

from diyabet_takip import security
from diyabet_takip.db import bootstrap
from diyabet_takip.db import doctors as doctors_db
from diyabet_takip.db import patients as patients_db
from diyabet_takip.db import records as records_db
from diyabet_takip.db import reference as ref
from diyabet_takip.db.client import get_db_strict
from diyabet_takip.services import (
    alert_service,
    auth_service,
    compliance_service,
    insulin_service,
    measurement_service,
    recommendation_service,
    report_service,
    stats_service,
)

PASSED: list[str] = []
FAILED: list[str] = []


def check(name: str, condition: bool, detail: str = "") -> None:
    if condition:
        PASSED.append(name)
        print(f"  ✔ {name}")
    else:
        FAILED.append(f"{name}: {detail}")
        print(f"  ✘ {name}  {detail}")


def main() -> None:
    print("[1/9] Bağlantı")
    db = get_db_strict()
    check("MongoDB ping", db is not None)

    print("[2/9] Şema + seed")
    bootstrap.ensure_schema(db)
    bootstrap.seed_if_empty(db)
    check("seed kullanıcılar", db[bootstrap.USERS].count_documents({}) >= 2)

    doktor_user = db[bootstrap.USERS].find_one({"tc_kimlik_no": "11111111111"})
    doktor_profile = db[bootstrap.DOCTOR_PROFILES].find_one({"user_id": doktor_user["_id"]})
    hasta_user = db[bootstrap.USERS].find_one({"tc_kimlik_no": "22222222222"})
    hasta_profile = db[bootstrap.PATIENT_PROFILES].find_one({"user_id": hasta_user["_id"]})

    print("[3/9] Giriş doğrulama")
    bad = auth_service.authenticate("11111111111", "yanlis")
    check("yanlış şifre reddedilir", not bad["ok"])
    good = auth_service.authenticate("11111111111", "doktor123")
    check("doktor girişi", good["ok"] and good["rol"] == "Doktor")
    hasta_login = auth_service.authenticate("22222222222", "hasta123")
    check("hasta girişi", hasta_login["ok"] and hasta_login["rol"] == "Hasta")
    check("hasta profile id", hasta_login.get("patient_id") == hasta_profile["_id"])

    print("[4/9] Ölçüm + uyarı zinciri")
    value = 55.0  # hipoglisemi eşiği altı → Acil Uyarı
    now_hour = datetime.datetime.now().replace(hour=8, minute=5, second=0, microsecond=0)
    result = measurement_service.insert_measurement(
        hasta_profile["_id"], value, "Sabah", dt=now_hour
    )
    check("geçerli ölçüm kaydı", result["ok"] and result["gecerli"])
    alert_name = alert_service.evaluate_measurement(
        hasta_profile["_id"], value, now_hour.date()
    )
    check("hipoglisemi uyarısı", alert_name == "Acil Uyarı")

    late = datetime.datetime.now().replace(hour=23, minute=30, second=0, microsecond=0)
    out = measurement_service.insert_measurement(
        hasta_profile["_id"], 120.0, "Akşam", dt=late
    )
    check("saat dışı ölçüm işaretlenir", out["ok"] and not out["gecerli"])
    notif_count = db[bootstrap.NOTIFICATIONS].count_documents(
        {"kullanici_id": hasta_user["_id"]}
    )
    check("saat dışı ölçüm bildirimi", notif_count > 0)

    print("[5/9] İnsülin + uyum + istatistik servisleri")
    insulin_service.generate_for_day(hasta_profile["_id"], now_hour.date())
    rec_count = db[bootstrap.INSULIN_RECS].count_documents(
        {"hasta_id": hasta_profile["_id"], "tarih": bootstrap.date_at(now_hour.date())}
    )
    check("insülin önerileri üretildi", rec_count >= 1)

    dosya = insulin_service.dose_for(210)
    check("insülin doz kuralı (3.0)", dosya == 3.0)
    check("insülin doz kuralı (1.0)", insulin_service.dose_for(115) == 1.0)

    compliance = compliance_service.compute_for(hasta_profile["_id"], now_hour.date())
    check("uyum skoru hesaplandı", compliance is not None and compliance["genel_uyum_skoru"] >= 0)
    stats = stats_service.compute_for(hasta_profile["_id"], now_hour.date())
    check("günlük istatistik", stats is not None and stats["olcum_sayisi"] >= 1)

    rec = recommendation_service.recommend(95.0, ["Polifaji", "Polidipsi"])
    check("kural tabanlı öneri", rec is not None and rec["onerilen_diyet"])

    print("[6/9] Diyet/egzersiz + semptom + bildirimler")
    patients_db.upsert_diet_log(hasta_profile["_id"], now_hour.date(), True, "test")
    patients_db.upsert_exercise_log(hasta_profile["_id"], now_hour.date(), True, 30, "test")
    hist = records_db.diet_exercise_history(hasta_profile["_id"], limit=3)
    check("diyet/egzersiz geçmişi", bool(hist) and hist[0]["diyet_uygulandimi"] is True)

    options = ref.get_symptom_options()
    patients_db.record_symptoms_by_patient(
        hasta_profile["_id"], now_hour.date(), "Orta", "test", [options[0][0]]
    )
    syms = records_db.symptom_history(hasta_profile["_id"], limit=5)
    check("hasta semptom kaydı", bool(syms) and syms[0]["kaydeden"] == "Hasta Kaydı")

    print("[7/9] Doktor sorguları")
    patients_list = doctors_db.list_patients_for_doctor(doktor_profile["_id"])
    check("hasta listesi", any(p["hasta_id"] == hasta_profile["_id"] for p in patients_list))
    searched = doctors_db.search_patients_for_doctor(
        doktor_profile["_id"], name_filter="", min_bs=None, max_bs=None
    )
    check("arama listesi", bool(searched))

    dashboard = doctors_db.doctor_dashboard(doktor_profile["_id"])
    check("dashboard", dashboard and dashboard["toplam_hasta_sayisi"] >= 1)

    alerts = doctors_db.patient_alerts_for_doctor(doktor_profile["_id"])
    check("uyarı listesi", bool(alerts))
    if alerts:
        doctors_db.mark_alert_read(alerts[0]["uyari_id"])

    critical = doctors_db.critical_patients_for_doctor(doktor_profile["_id"])
    check("kritik hastalar listesi", isinstance(critical, list))

    note_ok = doctors_db.save_doctor_note(
        doktor_profile["_id"], hasta_profile["_id"], "Tansiyon",
        "Kan basıncı takip edilecek (v2 not testi).", "Yüksek", "Doktor ve Hasta",
    )
    check("doktor notu", note_ok is None and bool(records_db.shared_doctor_notes(hasta_profile["_id"])))

    appt = doctors_db.create_appointment(
        doktor_profile["_id"], "22222222222",
        datetime.date.today() + datetime.timedelta(days=3), "14:30", 30, "smoke",
    )
    check("randevu oluşturma", appt["ok"])
    patient_appts = patients_db.appointments_for_patient(hasta_profile["_id"])
    check("randevu listelenir (hasta)", bool(patient_appts))

    print("[8/9] Hasta ekleme + şifre güncelleme")
    new_result = doctors_db.add_patient(
        doktor_profile["_id"], "99999999999", "Smoke", "Test",
        f"smoke{int(datetime.datetime.now().timestamp())}@parcatest.com", "sifre123",
        datetime.date(1995, 3, 10), "Kadın", "Tip 1", datetime.date(2025, 1, 1), 80, 140,
    )
    check("yeni hasta ekleme", new_result["ok"])
    dup_result = doctors_db.add_patient(
        doktor_profile["_id"], "99999999999", "Smoke", "Test",
        "smoke2@parcatest.com", "sifre123",
        datetime.date(1995, 3, 10), "Kadın", "Tip 1", datetime.date(2025, 1, 1), 80, 140,
    )
    check("aynı TC ikinci kez reddedilir", not dup_result["ok"])

    pw_result = auth_service.change_password(
        hasta_user["_id"], "hasta123", "yeni_sifre456"
    )
    check("şifre güncelleme", pw_result["ok"])
    relogin = auth_service.authenticate("22222222222", "yeni_sifre456")
    check("yeni şifreyle giriş", relogin["ok"])
    auth_service.change_password(hasta_user["_id"], "yeni_sifre456", "hasta123")

    print("[9/9] Rapor + hash politikası")
    sections = report_service.build_report(
        hasta_profile["_id"],
        datetime.date.today() - datetime.timedelta(days=7),
        datetime.date.today(),
    )
    check("rapor bölümleri", any(s["bolum"] == "Genel Bilgiler" for s in sections))

    stored = db[bootstrap.USERS].find_one({"tc_kimlik_no": "11111111111"})["sifre_hash"]
    check("şifreler hash'li", security.is_hashed(stored))

    print()
    if FAILED:
        print(f"SONUÇ: {len(FAILED)} HATA")
        for f in FAILED:
            print("  -", f)
        sys.exit(1)
    print(f"SONUÇ: {len(PASSED)} test OK")


if __name__ == "__main__":
    main()
