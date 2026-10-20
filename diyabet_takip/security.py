"""Şifre saklama ve doğrulama (PBKDF2-HMAC-SHA256).

v1'te şifreler düz metin saklanıyordu. v2 ile birlikte:

- Yeni kayıtlar PBKDF2-SHA256 (başına tuz, 390000 tur) ile HASH'lenir.
- Giriş doğrulamasında eski düz metin şifreler de kabul edilir ve şifre
  ilk başarılı girişte SAYdam şekilde HASH'e dönüştürülür ("upgrade on login").
"""

from __future__ import annotations

import hashlib
import hmac
import secrets

PBKDF2_ITERATIONS = 390_000
_HASH_PREFIX = "pbkdf2_sha256"


def hash_password(plain: str) -> str:
    """Şifreyi PBKDF2-HMAC-SHA256 + tuz ile hash'ler."""
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256", plain.encode("utf-8"), bytes.fromhex(salt), PBKDF2_ITERATIONS
    )
    return f"{_HASH_PREFIX}${PBKDF2_ITERATIONS}${salt}${digest.hex()}"


def is_hashed(stored: str) -> bool:
    return isinstance(stored, str) and stored.startswith(f"{_HASH_PREFIX}$")


def verify_password(plain: str, stored: str) -> bool:
    """Girilen şifreyi saklanan değerle karşılaştırır.

    Saklanan değer hash'liyse PBKDF2 ile karşılaştırılır; düz metin ise
    (v1 geçişi) eşitlik kontrolü yapılır.
    """
    if is_hashed(stored):
        try:
            _, iterations, salt, expected = stored.split("$", 3)
            digest = hashlib.pbkdf2_hmac(
                "sha256", plain.encode("utf-8"), bytes.fromhex(salt), int(iterations)
            )
            return hmac.compare_digest(digest.hex(), expected)
        except (ValueError, TypeError):
            return False
    return hmac.compare_digest(str(stored), plain)
