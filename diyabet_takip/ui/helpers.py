"""Arayüz ortak yardımcıları: uygulama kök yolu, tarih biçimleri ve rapor etiketleri."""

from __future__ import annotations

import datetime
import pathlib

ASSETS = pathlib.Path(__file__).resolve().parent.parent.parent / "assets"

REPORT_LABELS = {
    "hasta_adi": "Ad Soyad",
    "tc_kimlik": "T.C. Kimlik No",
    "diyabet_tipi": "Diyabet Tipi",
    "tani_tarihi": "Tanı Tarihi",
    "doktor_adi": "Doktor",
    "rapor_araligi": "Rapor Aralığı",
    "ortalama": "Ortalama Kan Şekeri",
    "minimum": "Minimum Kan Şekeri",
    "maksimum": "Maksimum Kan Şekeri",
    "olcum_sayisi": "Ölçüm Sayısı",
    "normal_aralik_uyum": "Normal Aralık Uyumu",
    "ortalama_diyet_uyum": "Ortalama Diyet Uyumu",
    "ortalama_egzersiz_uyum": "Ortalama Egzersiz Uyumu",
    "ortalama_olcum_uyum": "Ortalama Ölçüm Uyumu",
    "genel_uyum_skoru": "Genel Uyum Skoru",
    "toplam_uyari": "Toplam Uyarı",
    "acil_uyari": "Acil Uyarı",
    "hiperglisemi_uyari": "Hiperglisemi Uyarısı",
    "olcum_eksik_uyari": "Ölçüm Eksikliği Uyarısı",
}

PERCENT_KEYS = {
    "normal_aralik_uyum",
    "ortalama_diyet_uyum",
    "ortalama_egzersiz_uyum",
    "ortalama_olcum_uyum",
    "genel_uyum_skoru",
}
GLUCOSE_KEYS = {"ortalama", "minimum", "maksimum"}
COUNT_KEYS = {"olcum_sayisi", "toplam_uyari", "acil_uyari", "hiperglisemi_uyari", "olcum_eksik_uyari"}


def date_label(dt) -> str:
    return dt.strftime("%d.%m.%Y") if dt else "—"


def datetime_label(dt) -> str:
    return dt.strftime("%d.%m.%Y %H:%M") if dt else "—"


def _format_date(value) -> str:
    if isinstance(value, datetime.date):
        return value.strftime("%d.%m.%Y")
    try:
        return datetime.date.fromisoformat(str(value)).strftime("%d.%m.%Y")
    except ValueError:
        return str(value)


def format_report_value(key, value) -> str:
    """Rapor alanını okunur metne çevirir (yüzde, mg/dL, adet, tarih aralığı)."""
    if value is None:
        return "—"
    if key == "rapor_araligi" and isinstance(value, dict):
        return (
            f"{_format_date(value.get('baslangic'))} – "
            f"{_format_date(value.get('bitis'))}"
        )
    if key == "tani_tarihi":
        return _format_date(value)
    if key in GLUCOSE_KEYS and isinstance(value, (int, float)):
        return f"{value:.1f} mg/dL"
    if key in PERCENT_KEYS and isinstance(value, (int, float)):
        return f"%{value:.1f}"
    if key in COUNT_KEYS and isinstance(value, (int, float)):
        return f"{value:g} adet"
    return str(value)
