"""Cryptographic helpers: token hashing, JWT sessions, Telegram initData
validation, safe filenames."""

from __future__ import annotations

import hashlib
import hmac
import re
import secrets
import time
import unicodedata
from typing import Any
from urllib.parse import parse_qsl

import jwt

from .config import settings
from .errors import AuthError

# ── Device / opaque token hashing ────────────────────────────────────────────


def hash_token(token: str) -> str:
    """SHA-256 hex digest of a device token. Only the hash is stored."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def verify_token(token: str, token_hash: str) -> bool:
    return hmac.compare_digest(hash_token(token), token_hash)


def generate_device_token() -> str:
    return secrets.token_urlsafe(32)


# ── JWT server sessions (Mini App) ───────────────────────────────────────────


def create_access_token(telegram_user_id: int, role: str) -> str:
    now = int(time.time())
    payload = {
        "sub": str(telegram_user_id),
        "role": role,
        "iat": now,
        "exp": now + settings.access_token_ttl_seconds,
    }
    return jwt.encode(payload, settings.secret_key, algorithm="HS256")


def decode_access_token(token: str) -> dict[str, Any]:
    try:
        return jwt.decode(token, settings.secret_key, algorithms=["HS256"])
    except jwt.ExpiredSignatureError as exc:  # pragma: no cover - trivial
        raise AuthError("Сессия истекла. Откройте приложение заново.") from exc
    except jwt.InvalidTokenError as exc:
        raise AuthError("Недействительный токен.") from exc


# ── Telegram Mini App initData validation ────────────────────────────────────
# https://core.telegram.org/bots/webapps#validating-data-received-via-the-mini-app


def validate_init_data(
    init_data: str,
    bot_token: str,
    *,
    max_age_seconds: int | None = None,
) -> dict[str, Any]:
    """Validate Telegram WebApp ``initData`` and return its parsed fields.

    Raises :class:`AuthError` if the HMAC signature is invalid or the data is too
    old. NEVER trust ``initDataUnsafe`` on the client — only this function's
    result is authoritative.
    """
    if not bot_token:
        raise AuthError("Сервер не настроен для Mini App.")
    if not init_data:
        raise AuthError("Отсутствуют данные авторизации.")

    pairs = dict(parse_qsl(init_data, keep_blank_values=True))
    received_hash = pairs.pop("hash", None)
    if not received_hash:
        raise AuthError("Подпись отсутствует.")

    data_check_string = "\n".join(f"{k}={pairs[k]}" for k in sorted(pairs.keys()))
    secret_key = hmac.new(b"WebAppData", bot_token.encode(), hashlib.sha256).digest()
    computed = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()

    if not hmac.compare_digest(computed, received_hash):
        raise AuthError("Неверная подпись данных Telegram.")

    max_age = max_age_seconds if max_age_seconds is not None else settings.initdata_max_age_seconds
    auth_date = pairs.get("auth_date")
    if auth_date is not None:
        try:
            age = time.time() - int(auth_date)
        except ValueError as exc:
            raise AuthError("Некорректная дата авторизации.") from exc
        if age > max_age:
            raise AuthError("Данные авторизации устарели. Откройте приложение заново.")

    return pairs


# ── Safe filenames / path-traversal protection ───────────────────────────────

_SAFE_CHARS = re.compile(r"[^A-Za-z0-9._-]+")


def safe_filename(name: str, *, default: str = "audio") -> str:
    """Produce a filesystem-safe basename. Strips directories and traversal."""
    # Drop any directory component (defends against ../ and absolute paths).
    name = name.replace("\\", "/").split("/")[-1]
    name = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode()
    name = _SAFE_CHARS.sub("_", name).strip("._")
    name = name.lstrip(".")  # no leading dots -> no hidden/relative names
    if not name or name in {".", ".."}:
        return default
    return name[:120]
