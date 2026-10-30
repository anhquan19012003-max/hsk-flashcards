"""Encryption for the question bank (see specs/mock-tests.md section 5).

key  = PBKDF2-HMAC-SHA256(password, salt, ITERATIONS) -> 32 bytes (AES-256-GCM key)
file = MAGIC (4 bytes) + IV (12 random bytes) + AES-GCM ciphertext (tag appended)
The browser does the same with the Web Crypto API (docs/js/bankcrypto.js).
"""
import base64
import hashlib
import json
import os
from pathlib import Path

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

MAGIC = b"HSKB"
ITERATIONS = 310_000
FORMAT_VERSION = 1
CHECK_PLAINTEXT = b"hsk-bank-ok"


def b64(data: bytes) -> str:
    return base64.b64encode(data).decode("ascii")


def b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode("ascii").rstrip("=")


def derive_key(password: str, salt: bytes, iterations: int = ITERATIONS) -> bytes:
    kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=salt, iterations=iterations)
    return kdf.derive(password.encode("utf-8"))


def encrypt(key: bytes, plaintext: bytes) -> bytes:
    iv = os.urandom(12)
    return MAGIC + iv + AESGCM(key).encrypt(iv, plaintext, None)


def decrypt(key: bytes, blob: bytes) -> bytes:
    if blob[:4] != MAGIC:
        raise ValueError("missing magic header")
    return AESGCM(key).decrypt(blob[4:16], blob[16:], None)


def media_name(salt: bytes, kind: str, item_id: str) -> str:
    """Opaque file name for a clip/image: hash of its id + salt (names reveal nothing)."""
    return hashlib.sha256(salt + f"{kind}:{item_id}".encode("utf-8")).hexdigest()[:32]


def make_meta(key: bytes, salt: bytes, levels, iterations: int = ITERATIONS) -> dict:
    return {
        "v": FORMAT_VERSION,
        "salt": b64(salt),
        "iter": iterations,
        "levels": sorted(levels),
        "check": b64(encrypt(key, CHECK_PLAINTEXT)),
    }


def key_matches_meta(key: bytes, meta: dict) -> bool:
    try:
        return decrypt(key, base64.b64decode(meta["check"])) == CHECK_PLAINTEXT
    except Exception:
        return False


def read_meta(path: Path):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
