"""Uygulama yapılandırması.

Ayarlar ortam değişkenlerinden (ve varsa proje kökündeki ``.env`` dosyasından)
okunur:

- ``MONGODB_URI``     : bağlantı URI'si (örn. ``mongodb://localhost:27017``)
- ``MONGODB_HOST``    : URI verilmediyse kullanılır (varsayılan ``localhost``)
- ``MONGODB_PORT``    : URI verilmediyse kullanılır (varsayılan ``27017``)
- ``MONGODB_DB``      : veritabanı adı (varsayılan ``diyabet_takip``)
"""

from __future__ import annotations

import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def _load_dotenv(path: Path) -> None:
    """Çok basit bir ``.env`` okuyucu (ek bağımlılık istemiyoruz)."""
    if not path.is_file():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip().strip("'\"")
        os.environ.setdefault(key, value)


_load_dotenv(PROJECT_ROOT / ".env")

MONGODB_URI: str = os.environ.get("MONGODB_URI", "")
MONGODB_HOST: str = os.environ.get("MONGODB_HOST", "localhost")
MONGODB_PORT: int = int(os.environ.get("MONGODB_PORT", "27017"))
MONGODB_DB: str = os.environ.get("MONGODB_DB", "diyabet_takip")

#: Bağlantı hatasında kullanıcının göreceği yardımcı mesaj.
DB_HINT = (
    "MongoDB sunucusuna ulaşılamadı. mongod'un çalıştığından ve "
    "MONGODB_URI / MONGODB_HOST / MONGODB_PORT ayarlarının doğru olduğundan emin olun."
)
