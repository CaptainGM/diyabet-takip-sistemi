"""Oturum durumu.

v1'de bu değerler ``global`` değişkenlerdi; v2'de tek bir oturum nesnesi
içinde toplanarak modüller arası geçiş güvenli hale getirildi.
"""

from __future__ import annotations


class Session:
    """Aktif oturuma ait kimlik ve pencere referansları."""

    def __init__(self) -> None:
        self.window = None  # tk.Tk referansı (app.py içinde atanır)
        self.user_id = None  # users _id
        self.user_ad: str | None = None
        self.user_soyad: str | None = None
        self.user_role: str | None = None  # "Doktor" | "Hasta"
        self.patient_id = None  # patients koleksiyon _id (hasta ise)
        self.doctor_id = None  # doctor_profiles koleksiyon _id (doktor ise)

    def reset(self) -> None:
        self.user_id = None
        self.user_ad = None
        self.user_soyad = None
        self.user_role = None
        self.patient_id = None
        self.doctor_id = None

    @property
    def full_name(self) -> str:
        return " ".join(x for x in (self.user_ad, self.user_soyad) if x)


session = Session()
