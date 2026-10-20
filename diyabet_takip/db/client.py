"""MongoDB bağlantısı ve yardımcı dönüşümleri."""

from __future__ import annotations

import datetime
import tkinter as tk
from tkinter import messagebox

import pymongo
from pymongo import MongoClient
from pymongo.database import Database

from .. import config


class DBError(Exception):
    pass


_client: MongoClient | None = None


def get_client() -> MongoClient:
    """Paylaşımlı MongoClient (lazy)."""
    global _client
    if _client is None:
        uri = config.MONGODB_URI or f"mongodb://{config.MONGODB_HOST}:{config.MONGODB_PORT}"
        try:
            client = MongoClient(
                uri,
                serverSelectionTimeoutMS=8000,
                appname="diyabet-takip-sistemi",
            )
            client.admin.command("ping")
            _client = client
        except pymongo.errors.PyMongoError as exc:  # bağlantı gelmezse anla
            raise DBError(f"{config.DB_HINT}\n\nDetay: {exc}") from exc
    return _client


def get_db() -> Database | None:
    """Veritabanı (Database | None). Bağlantı yoksa GUI uyarısı gösterir."""
    try:
        return get_client()[config.MONGODB_DB]
    except DBError as exc:
        event_root = tk._get_default_root()
        messagebox.showerror("Veritabanı Bağlantı Hatası", str(exc), parent=event_root)
        return None


def get_db_strict() -> Database:
    """Scriptler/servisler için: hata yükseltir, sessiz kalmaz."""
    return get_client()[config.MONGODB_DB]


def db_name_available() -> bool:
    try:
        get_client()
        return True
    except DBError:
        return False


# --- Dönüşüm yardımcıları -------------------------------------------------
def as_date(dt: datetime.datetime | None) -> datetime.date | None:
    """pymongo datetime → datetime.date (UI strftime çağrıları için)."""
    return dt.date() if isinstance(dt, datetime.datetime) else None


def as_time(dt: datetime.datetime | None) -> datetime.time | None:
    return dt.time() if isinstance(dt, datetime.datetime) else None


def date_at(dt_date: datetime.date) -> datetime.datetime:
    """Tarihi UTC'siz (naive) geceyarı datetime'ına çevirir."""
    return datetime.datetime(dt_date.year, dt_date.month, dt_date.day)


def today() -> datetime.date:
    return datetime.date.today()


def now() -> datetime.datetime:
    return datetime.datetime.now()
