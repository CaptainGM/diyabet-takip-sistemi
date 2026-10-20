"""Ölçüm kaydı zinciri: kayıt → uyarı/bildirim → insülin önerisi → skorlar.

v1'de bu zincir MySQL trigger'ı (``kan_sekeri_uyari_kontrol``) +PROCEDURE
``insulin_onerisi_olustur`` + events ile çalışıyordu. v2'de tek bir uygulama
katmanı fonksiyonu koordine eder (transaction destekleniyorsa atomic).
"""

from __future__ import annotations

import datetime

from ..db import bootstrap as B
from ..db.client import get_db
from . import alert_service, compliance_service, insulin_service, stats_service

# Ölçüm zamanı pencereleri (saat bazında geçerlilik)
MEAL_WINDOWS = {
    "Sabah": (7, 9),
    "Öğle": (12, 14),
    "İkindi": (15, 17),
    "Akşam": (18, 20),
    "Gece": (22, 24),
}


def is_on_time(dt: datetime.datetime, tip: str) -> bool:
    window = MEAL_WINDOWS.get(tip)
    if not window:
        return True
    start, end = window
    return start <= dt.hour < end


def insert_measurement(
    hasta_id,
    value: float,
    olcum_tipi: str,
    dt: datetime.datetime | None = None,
    notlar: str = "",
) -> dict:
    """Ölçümü kaydeder ve yan işlemleri çalıştırır.

    Dönen dict: {ok, mesaj, gecerli, uyari_adi?}
    """
    db = get_db()
    if db is None:
        return {"ok": False, "mesaj": "Veritabanı bağlantı hatası."}

    if not 0 <= value <= 1000:
        return {"ok": False, "mesaj": "Kan şekeri değeri 0 ile 1000 arasında olmalıdır."}

    dt = dt or datetime.datetime.now()
    gecerli = is_on_time(dt, olcum_tipi)

    result = db[B.MEASUREMENTS].insert_one(
        {
            "hasta_id": hasta_id,
            "olcum_zamani": dt,
            "kan_sekeri_degeri": float(value),
            "olcum_tipi": olcum_tipi,
            "gecerli": gecerli,
            "notlar": notlar,
            "kayit_zamani": datetime.datetime.now(),
        }
    )

    mesaj = f"Kan şekeri ölçümü başarıyla kaydedildi! ({value:g} mg/dL)"
    if not gecerli:
        start, end = MEAL_WINDOWS[olcum_tipi]
        mesaj = (
            f"Ölçümünüz kaydedildi, ancak {olcum_tipi} ölçümü için önerilen saat "
            f"aralığı dışındadır ({start:02d}:00-{end:02d}:00).\n"
            "Bu ölçüm ortalama hesabına DAHİL EDİLMEYECEKTİR."
        )
        alert_service.notify_out_of_window(hasta_id, value, dt)

    insulin_service.update_recommendation(hasta_id, dt.date(), olcum_tipi)
    compliance_service.compute_for(hasta_id, dt.date())
    stats_service.compute_for(hasta_id, dt.date())

    if gecerli:
        alert_service.evaluate_measurement(hasta_id, value, dt.date())

    return {"ok": True, "mesaj": mesaj, "gecerli": gecerli, "olcum_id": result.inserted_id}
