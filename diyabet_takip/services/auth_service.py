"""Giriş/doğrulama servisi — PBKDF2 hash doğrulama + v1 geçiş yükseltmesi."""

from __future__ import annotations

import datetime

from .. import security
from ..db import bootstrap as B
from ..db.client import get_db
from ..db.reference import find_patient_profile_id


def authenticate(tc_no: str, password: str) -> dict:
    """Giriş dener. Dönen dict: {ok, mesaj, rol, user_id, ad, soyad}."""
    db = get_db()
    if db is None:
        return {"ok": False, "mesaj": "Veritabanı bağlantı hatası."}

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


def change_password(user_id, current_plain: str, new_plain: str) -> dict:
    """Profil ekranının şifre değiştirme akışı."""
    db = get_db()
    if db is None:
        return {"ok": False, "mesaj": "Veritabanı bağlantı hatası."}
    user = db[B.USERS].find_one({"_id": user_id})
    if not user:
        return {"ok": False, "mesaj": "Kullanıcı bulunamadı."}
    if not security.verify_password(current_plain, user.get("sifre_hash", "")):
        return {"ok": False, "mesaj": "Mevcut şifre doğru değil."}
    if len(new_plain) < 6 or len(new_plain) > 40:
        return {"ok": False, "mesaj": "Yeni şifre 6-40 karakter arası olmalıdır."}
    db[B.USERS].update_one(
        {"_id": user_id}, {"$set": {"sifre_hash": security.hash_password(new_plain)}}
    )
    return {"ok": True, "mesaj": "Şifreniz güncellendi."}
