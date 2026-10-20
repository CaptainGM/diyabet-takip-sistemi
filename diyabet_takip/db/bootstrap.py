"""Koleksiyon adları, indeksler ve şema kurulumu (mongod tarafı)."""

from __future__ import annotations

import datetime

from pymongo.database import Database

from .. import security
from .client import date_at, get_db_strict

USERS = "users"
DOCTOR_PROFILES = "doctor_profiles"
PATIENT_PROFILES = "patient_profiles"
DIET_TYPES = "diet_types"
EXERCISE_TYPES = "exercise_types"
SYMPTOM_TYPES = "symptom_types"
MEASUREMENTS = "measurements"
DIET_PLANS = "diet_plans"
EXERCISE_PLANS = "exercise_plans"
DIET_LOGS = "diet_logs"
EXERCISE_LOGS = "exercise_logs"
INSULIN_RECS = "insulin_recommendations"
ALERT_TYPES = "alert_types"
ALERTS = "alerts"
NOTIFICATIONS = "notifications"
DOCTOR_NOTES = "doctor_notes"
COMPLIANCE_SCORES = "compliance_scores"
APPOINTMENTS = "appointments"
SYSTEM_SETTINGS = "system_settings"
RULE_BASE = "rule_base"
BLOOD_SUGAR_STATS = "blood_sugar_stats"
SYMPTOM_RECORDS = "symptom_records"  # v1 tablosu: hasta_belirtileri


def _ensure_index(db: Database, collection: str, keys, unique: bool = False) -> None:
    db[collection].create_index(keys, unique=unique)


def ensure_schema(db: Database | None = None) -> None:
    """Collection'ları ve indeksleri oluşturur (idempotent)."""
    if db is None:
        db = get_db_strict()

    _ensure_index(db, USERS, "tc_kimlik_no", unique=True)
    _ensure_index(db, USERS, "eposta", unique=True)
    _ensure_index(db, USERS, "rol")
    _ensure_index(db, DOCTOR_PROFILES, "user_id", unique=True)
    _ensure_index(db, PATIENT_PROFILES, "user_id", unique=True)
    _ensure_index(db, PATIENT_PROFILES, "doktor_id")

    _ensure_index(db, MEASUREMENTS, [("hasta_id", 1), ("olcum_zamani", -1)])
    _ensure_index(db, MEASUREMENTS, [("hasta_id", 1), ("olcum_zamani", 1)])
    _ensure_index(db, MEASUREMENTS, [("hasta_id", 1), ("gecerli", 1), ("olcum_zamani", -1)])

    _ensure_index(db, DIET_LOGS, [("hasta_id", 1), ("takip_tarihi", -1)], unique=True)
    _ensure_index(db, EXERCISE_LOGS, [("hasta_id", 1), ("takip_tarihi", -1)], unique=True)
    _ensure_index(db, DIET_PLANS, [("hasta_id", 1), ("aktif_durum", 1)])
    _ensure_index(db, EXERCISE_PLANS, [("hasta_id", 1), ("aktif_durum", 1)])

    _ensure_index(
        db, INSULIN_RECS, [("hasta_id", 1), ("tarih", 1), ("olcum_tipi", 1)], unique=True
    )
    _ensure_index(db, INSULIN_RECS, [("hasta_id", 1), ("tarih", -1)])

    _ensure_index(db, ALERTS, [("doktor_id", 1), ("okundu", 1), ("olusturma_tarihi", -1)])
    _ensure_index(db, ALERTS, [("hasta_id", 1), ("uyari_tarihi", -1)])
    _ensure_index(db, NOTIFICATIONS, [("kullanici_id", 1), ("olusturma_tarihi", -1)])
    _ensure_index(db, DOCTOR_NOTES, [("hasta_id", 1), ("olusturma_tarihi", -1)])
    _ensure_index(db, SYMPTOM_RECORDS, [("hasta_id", 1), ("kayit_tarihi", -1)])
    _ensure_index(
        db, SYMPTOM_RECORDS,
        [("hasta_id", 1), ("belirti_id", 1), ("kayit_tarihi", 1)],
        unique=True,
    )
    _ensure_index(
        db, BLOOD_SUGAR_STATS, [("hasta_id", 1), ("istatistik_tarihi", -1)], unique=True
    )

    _ensure_index(db, COMPLIANCE_SCORES, [("hasta_id", 1), ("hesaplama_tarihi", -1)], unique=True)
    _ensure_index(db, APPOINTMENTS, [("doktor_id", 1), ("randevu_tarihi", -1)])
    _ensure_index(db, APPOINTMENTS, [("hasta_id", 1), ("randevu_tarihi", -1)])

    _ensure_index(db, ALERT_TYPES, "uyari_adi", unique=True)
    _ensure_index(db, DIET_TYPES, "diyet_adi", unique=True)
    _ensure_index(db, EXERCISE_TYPES, "egzersiz_adi", unique=True)
    _ensure_index(db, SYMPTOM_TYPES, "belirti_adi", unique=True)
    _ensure_index(db, SYSTEM_SETTINGS, "anahtar", unique=True)

    _ensure_fields_for_mongo(db)


def _ensure_fields_for_mongo(db: Database) -> None:
    """v1'de MySQL ENUM/CHECK ile korunan sınırlar; burada kayıt sırasında
    uygulama katmanıyor. (Şema uyumu için bilgisel fonksiyon.)"""
    # collections listelenerek collection varsa oluşturulur:
    for name in (
        USERS, DOCTOR_PROFILES, PATIENT_PROFILES, DIET_TYPES, EXERCISE_TYPES,
        SYMPTOM_TYPES, MEASUREMENTS, DIET_PLANS, EXERCISE_PLANS, DIET_LOGS,
        EXERCISE_LOGS, INSULIN_RECS, ALERT_TYPES, ALERTS, NOTIFICATIONS,
        DOCTOR_NOTES, COMPLIANCE_SCORES, APPOINTMENTS, SYSTEM_SETTINGS, RULE_BASE,
        SYMPTOM_RECORDS, BLOOD_SUGAR_STATS,
    ):
        if name not in db.list_collection_names():
            db.create_collection(name)


def seed_if_empty(db: Database | None = None) -> None:
    """Demo kullanıcılar ve referans verileri (halihazırda boşsa)."""
    if db is None:
        db = get_db_strict()
    if db[USERS].count_documents({}) > 0:
        return

    now = datetime.datetime.now()
    doctor_user_id = db[USERS].insert_one(
        {
            "tc_kimlik_no": "11111111111",
            "ad": "Dr. Ahmet",
            "soyad": "Yılmaz",
            "dogum_tarihi": date_at(datetime.date(1980, 1, 1)),
            "cinsiyet": "Erkek",
            "eposta": "ahmet.yilmaz@ornek.com",
            "sifre_hash": security.hash_password("doktor123"),
            "rol": "Doktor",
            "aktif_durum": True,
            "kayit_tarihi": now,
            "son_giris_tarihi": None,
        }
    ).inserted_id
    db[DOCTOR_PROFILES].insert_one(
        {
            "user_id": doctor_user_id,
            "uzmanlik_alani": "Endokrinoloji",
            "diploma_no": "DIP001",
        }
    )

    patient_user_id = db[USERS].insert_one(
        {
            "tc_kimlik_no": "22222222222",
            "ad": "Mehmet",
            "soyad": "Demir",
            "dogum_tarihi": date_at(datetime.date(1990, 5, 15)),
            "cinsiyet": "Erkek",
            "eposta": "mehmet.demir@ornek.com",
            "sifre_hash": security.hash_password("hasta123"),
            "rol": "Hasta",
            "aktif_durum": True,
            "kayit_tarihi": now,
            "son_giris_tarihi": None,
        }
    ).inserted_id
    doctor_profile = db[DOCTOR_PROFILES].find_one({"user_id": doctor_user_id})
    db[PATIENT_PROFILES].insert_one(
        {
            "user_id": patient_user_id,
            "doktor_id": doctor_profile["_id"],
            "tani_tarihi": date_at(datetime.date(2024, 1, 15)),
            "diyabet_tipi": "Tip 2",
            "hedef_kan_sekeri_min": 70,
            "hedef_kan_sekeri_max": 110,
            "notlar": "",
        }
    )

    seed_reference_data(db)


def seed_reference_data(db: Database) -> None:
    """Türler, eşik ayarları ve kural tabanı."""
    if db[DIET_TYPES].count_documents({}) == 0:
        db[DIET_TYPES].insert_many(
            [
                {
                    "diyet_adi": "Az Şekerli Diyet",
                    "aciklama": "Şekerli gıdalar sınırlanır, kompleks karbonhidratlara öncelik "
                    "verilir. Lifli gıdalar ve düşük glisemik indeksli besinler tercih edilir.",
                },
                {
                    "diyet_adi": "Şekersiz Diyet",
                    "aciklama": "Rafine şeker ve şeker katkılı tüm ürünler tamamen dışlanır. "
                    "Hiperglisemi riski taşıyan bireylerde önerilir.",
                },
                {
                    "diyet_adi": "Dengeli Beslenme",
                    "aciklama": "Diyabetli bireylerin yaşam tarzına uygun, dengeli ve sürdürülebilir "
                    "bir diyet yaklaşımıdır. Porsiyon kontrolü, mevsimsel taze ürünler ve su "
                    "tüketimi temel unsurlardır.",
                },
            ]
        )

    if db[EXERCISE_TYPES].count_documents({}) == 0:
        db[EXERCISE_TYPES].insert_many(
            [
                {
                    "egzersiz_adi": "Yürüyüş",
                    "aciklama": "Hafif tempolu, günlük yapılabilecek bir egzersizdir.",
                },
                {
                    "egzersiz_adi": "Bisiklet",
                    "aciklama": "Alt vücut kaslarını çalıştırır; dış mekanda veya sabit bisikletle "
                    "uygulanabilir.",
                },
                {
                    "egzersiz_adi": "Klinik Egzersiz",
                    "aciklama": "Doktor tarafından verilen belirli hareketleri içeren planlı "
                    "egzersizlerdir. Stresin azaltılması ve hareket kabiliyetinin artırılması "
                    "amaçlanır.",
                },
            ]
        )

    if db[SYMPTOM_TYPES].count_documents({}) == 0:
        db[SYMPTOM_TYPES].insert_many(
            [
                {"belirti_adi": "Poliüri", "aciklama": "Sık idrara çıkma"},
                {"belirti_adi": "Polifaji", "aciklama": "Aşırı açlık hissi"},
                {"belirti_adi": "Polidipsi", "aciklama": "Aşırı susama hissi"},
                {
                    "belirti_adi": "Nöropati",
                    "aciklama": "El ve ayaklarda karıncalanma veya uyuşma hissi",
                },
                {"belirti_adi": "Kilo kaybı", "aciklama": "Ani kilo kaybı"},
                {"belirti_adi": "Yorgunluk", "aciklama": "Sürekli yorgunluk hissi"},
                {
                    "belirti_adi": "Yaraların yavaş iyileşmesi",
                    "aciklama": "Yaraların normal sürede iyileşmemesi",
                },
                {"belirti_adi": "Bulanık görme", "aciklama": "Görme bozukluğu"},
            ]
        )

    if db[ALERT_TYPES].count_documents({}) == 0:
        db[ALERT_TYPES].insert_many(
            [
                {
                    "uyari_adi": "Acil Uyarı",
                    "aciklama": "Kan şekeri kritik seviyenin altına düştü. Hipoglisemi riski!",
                    "aciliyet_seviyesi": "Kritik",
                },
                {
                    "uyari_adi": "Takip Uyarısı",
                    "aciklama": "Kan şekeri orta yüksek seviyede. Durum izlenmeli.",
                    "aciliyet_seviyesi": "Orta",
                },
                {
                    "uyari_adi": "İzleme Uyarısı",
                    "aciklama": "Kan şekeri yüksek seviyede. Diyabet kontrolü gereklidir.",
                    "aciliyet_seviyesi": "Yüksek",
                },
                {
                    "uyari_adi": "Acil Müdahale Uyarısı",
                    "aciklama": "Kan şekeri kritik seviyenin üzerinde. Hiperglisemi durumu.",
                    "aciliyet_seviyesi": "Kritik",
                },
                {
                    "uyari_adi": "Ölçüm Eksik Uyarısı",
                    "aciklama": "Hasta gün boyunca kan şekeri ölçümü yapmamıştır.",
                    "aciliyet_seviyesi": "Yüksek",
                },
                {
                    "uyari_adi": "Ölçüm Yetersiz Uyarısı",
                    "aciklama": "Hastanın günlük ölçüm sayısı yetersizdir.",
                    "aciliyet_seviyesi": "Orta",
                },
            ]
        )

    if db[SYSTEM_SETTINGS].count_documents({}) == 0:
        db[SYSTEM_SETTINGS].insert_many(
            [
                {
                    "anahtar": "olcum_hatirlatma_saatleri",
                    "deger": ["07:00", "12:00", "15:00", "18:00", "22:00"],
                    "aciklama": "Kan şekeri ölçüm hatırlatma saatleri",
                    "tip": "json",
                },
                {
                    "anahtar": "hipoglisemi_esik",
                    "deger": 70,
                    "aciklama": "Hipoglisemi uyarı eşiği (mg/dL)",
                    "tip": "number",
                },
                {
                    "anahtar": "hiperglisemi_esik",
                    "deger": 200,
                    "aciklama": "Hiperglisemi uyarı eşiği (mg/dL)",
                    "tip": "number",
                },
                {
                    "anahtar": "minimum_gunluk_olcum",
                    "deger": 3,
                    "aciklama": "Minimum günlük ölçüm sayısı",
                    "tip": "number",
                },
            ]
        )

    if db[RULE_BASE].count_documents({}) == 0:
        diyet_map = {
            d["diyet_adi"]: d["_id"] for d in db[DIET_TYPES].find({}, {"diyet_adi": 1})
        }
        egz_map = {
            e["egzersiz_adi"]: e["_id"] for e in db[EXERCISE_TYPES].find({}, {"egzersiz_adi": 1})
        }

        def rule(ks_min, ks_max, belirtiler, diyet, egzersiz=None):
            return {
                "kan_sekeri_min": ks_min,
                "kan_sekeri_max": ks_max,
                "belirtiler": belirtiler,
                "onerilen_diyet": diyet,
                "onerilen_diyet_id": diyet_map.get(diyet),
                "onerilen_egzersiz": egzersiz,
                "onerilen_egzersiz_id": egz_map.get(egzersiz) if egzersiz else None,
                "aktif_durum": True,
            }

        db[RULE_BASE].insert_many(
            [
                rule(0, 69.99, ["Nöropati", "Polifaji", "Yorgunluk"], "Dengeli Beslenme"),
                rule(0, 69.99, ["Yorgunluk", "Kilo kaybı"], "Az Şekerli Diyet", "Yürüyüş"),
                rule(70, 110, ["Polifaji", "Polidipsi"], "Dengeli Beslenme", "Yürüyüş"),
                rule(70, 110, ["Bulanık görme", "Nöropati"], "Az Şekerli Diyet", "Klinik Egzersiz"),
                rule(70, 110, ["Poliüri", "Polidipsi"], "Şekersiz Diyet", "Klinik Egzersiz"),
                rule(110.01, 180, ["Yorgunluk", "Nöropati", "Bulanık görme"], "Az Şekerli Diyet", "Yürüyüş"),
                rule(110.01, 180, ["Yaraların yavaş iyileşmesi", "Polifaji", "Polidipsi"], "Şekersiz Diyet", "Klinik Egzersiz"),
                rule(180.01, 999.99, ["Yaraların yavaş iyileşmesi", "Kilo kaybı"], "Şekersiz Diyet", "Yürüyüş"),
            ]
        )
