"""Giriş/doğrulama servisi — PBKDF2 hash doğrulama + v1 geçiş yükseltmesi."""

from __future__ import annotations

import datetime

from .. import security
from ..db import bootstrap as B
from ..db.client import date_at, get_db
from ..db.reference import find_patient_profile_id


def authenticate(tc_no: str, password: str) -> dict:
    """Giriş dener. Dönen dict: {ok, mesaj, rol, user_id, ad, soyad}."""
    db = get_db()
    if db is None:
        return {"ok": False, "mesaj": "Giriş hizmetine şu anda ulaşılamıyor. Lütfen biraz sonra tekrar deneyin."}

    if not tc_no or not password:
        return {"ok": False, "mesaj": "T.C. Kimlik No ve Şifre boş bırakılamaz!"}
    if not tc_no.isdigit() or len(tc_no) != 11:
        return {"ok": False, "mesaj": "T.C. Kimlik No 11 haneli sayı olmalıdır!"}

    user = db[B.USERS].find_one({"tc_kimlik_no": tc_no, "rol": {"$exists": True}})
    if not user or not user.get("aktif_durum", True):
        return {"ok": False, "mesaj": "Yanlış T.C. Kimlik No veya Şifre."}

    stored = user.get("sifre_hash", "") or ""
    if not security.verify_password(password, stored):
        return {"ok": False, "mesaj": "Yanlış T.C. Kimlik No veya Şifre."}

    update: dict = {"son_giris_tarihi": datetime.datetime.now()}
    # v1 düz metin şifre → ilk girişte şeffaf yükseltme
    if not security.is_hashed(stored):
        update["sifre_hash"] = security.hash_password(password)
    db[B.USERS].update_one({"_id": user["_id"]}, {"$set": update})

    rol = user.get("rol")
    result: dict = {
        "ok": True,
        "rol": rol,
        "user_id": user["_id"],
        "ad": user.get("ad"),
        "soyad": user.get("soyad"),
    }
    if rol == "Hasta":
        pid = find_patient_profile_id(db, user["_id"])
        result["patient_id"] = pid
        result["mesaj"] = "Giriş başarılı."
    elif rol == "Doktor":
        prof = db[B.DOCTOR_PROFILES].find_one({"user_id": user["_id"]}, {"_id": 1})
        result["doctor_id"] = prof["_id"] if prof else None
        result["mesaj"] = "Giriş başarılı."
    else:
        result = {"ok": False, "mesaj": "Kullanıcı rolü tanımlanamadı."}
    return result


PASSWORD_RULES_TEXT = (
    "en az 8 karakter",
    "en az 1 büyük harf (A-Z)",
    "en az 1 küçük harf (a-z)",
    "en az 1 rakam (0-9)",
    "en az 1 özel karakter (!@#$%...)",
)


def validate_password(password: str) -> list[str]:
    """Şifre politikasını denetler; karşılanmayan kuralları döndürür."""
    missing: list[str] = []
    if len(password) < 8:
        missing.append(PASSWORD_RULES_TEXT[0])
    if not any(c.isupper() for c in password):
        missing.append(PASSWORD_RULES_TEXT[1])
    if not any(c.islower() for c in password):
        missing.append(PASSWORD_RULES_TEXT[2])
    if not any(c.isdigit() for c in password):
        missing.append(PASSWORD_RULES_TEXT[3])
    if not any(not c.isalnum() for c in password):
        missing.append(PASSWORD_RULES_TEXT[4])
    return missing


def register_user(
    tc_no: str,
    ad: str,
    soyad: str,
    eposta: str,
    plain_password: str,
    rol: str,
    *,
    diyabet_tipi: str = "Tip 2",
    hedef_min: int = 70,
    hedef_max: int = 180,
    uzmanlik: str = "Dahiliye",
) -> dict:
    """Giriş ekranındaki kendin kaydolma akışı (Hasta veya Doktor).

    - TC/e-posta benzersizliği denenir; şifre PBKDF2 hash ile saklanır.
    - Hasta: profili en az hastalı doktora otomatik atanır (varsa).
    - Doktor: boş doktor profili + uzmanlık ile açılır.
    """
    db = get_db()
    if db is None:
        return {"ok": False, "mesaj": "Giriş hizmetine şu anda ulaşılamıyor. Lütfen biraz sonra tekrar deneyin."}

    if not tc_no.isdigit() or len(tc_no) != 11:
        return {"ok": False, "mesaj": "T.C. Kimlik No 11 haneli sayı olmalıdır."}
    if "@" not in eposta or "." not in eposta.split("@")[-1]:
        return {"ok": False, "mesaj": "Geçerli bir e-posta adresi girin."}
    missing = validate_password(plain_password)
    if missing:
        return {
            "ok": False,
            "mesaj": "Şifre kuralları karşılanmıyor:\n- " + "\n- ".join(missing),
        }
    if rol not in ("Hasta", "Doktor"):
        return {"ok": False, "mesaj": "Rol seçimi geçersiz."}

    if db[B.USERS].find_one(
        {"$or": [{"tc_kimlik_no": tc_no}, {"eposta": eposta}]}, {"_id": 1}
    ):
        return {"ok": False, "mesaj": "Bu T.C. Kimlik No veya e-posta zaten kayıtlı."}

    now = datetime.datetime.now()
    user_id = db[B.USERS].insert_one(
        {
            "tc_kimlik_no": tc_no,
            "ad": ad.strip(),
            "soyad": soyad.strip(),
            "eposta": eposta.strip().lower(),
            "sifre_hash": security.hash_password(plain_password),
            "rol": rol,
            "aktif_durum": True,
            "kayit_tarihi": now,
            "son_giris_tarihi": None,
        }
    ).inserted_id

    if rol == "Hasta":
        # En az hastalı doktora otomatik atama (yoksa None kalır)
        doctor_agg = list(
            db[B.DOCTOR_PROFILES].aggregate(
                [
                    {
                        "$lookup": {
                            "from": B.PATIENT_PROFILES,
                            "localField": "_id",
                            "foreignField": "doktor_id",
                            "as": "hastalar",
                        }
                    },
                    {"$addFields": {"_sayi": {"$size": "$hastalar"}}},
                    {"$sort": {"_sayi": 1}},
                    {"$limit": 1},
                    {"$project": {"_id": 1}},
                ]
            )
        )
        doktor_id = doctor_agg[0]["_id"] if doctor_agg else None
        db[B.PATIENT_PROFILES].insert_one(
            {
                "user_id": user_id,
                "doktor_id": doktor_id,
                "tani_tarihi": date_at(datetime.date.today()),
                "diyabet_tipi": diyabet_tipi,
                "hedef_kan_sekeri_min": hedef_min,
                "hedef_kan_sekeri_max": hedef_max,
                "notlar": "",
            }
        )
    else:
        db[B.DOCTOR_PROFILES].insert_one(
            {
                "user_id": user_id,
                "uzmanlik_alani": uzmanlik,
                "hastane_adi": "",
                "kayit_tarihi": now,
            }
        )
    return {"ok": True, "mesaj": f"Hoş geldiniz {ad}! Hesabınız oluşturuldu."}


def change_password(user_id, current_plain: str, new_plain: str) -> dict:
    """Profil ekranının şifre değiştirme akışı."""
    db = get_db()
    if db is None:
        return {"ok": False, "mesaj": "Giriş hizmetine şu anda ulaşılamıyor. Lütfen biraz sonra tekrar deneyin."}
    user = db[B.USERS].find_one({"_id": user_id})
    if not user:
        return {"ok": False, "mesaj": "Kullanıcı bulunamadı."}
    if not security.verify_password(current_plain, user.get("sifre_hash", "")):
        return {"ok": False, "mesaj": "Mevcut şifre doğru değil."}
    missing = validate_password(new_plain)
    if missing:
        return {
            "ok": False,
            "mesaj": "Yeni şifre şu kuralları sağlamıyor:\n- " + "\n- ".join(missing),
        }
    db[B.USERS].update_one(
        {"_id": user_id}, {"$set": {"sifre_hash": security.hash_password(new_plain)}}
    )
    return {"ok": True, "mesaj": "Şifreniz güncellendi."}
