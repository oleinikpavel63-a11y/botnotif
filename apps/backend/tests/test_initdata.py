from __future__ import annotations

import hashlib
import hmac
import json
import time
from urllib.parse import urlencode

import pytest
from app.core.errors import AuthError
from app.core.security import validate_init_data

BOT_TOKEN = "123456:TEST-TOKEN"


def _sign(fields: dict, token: str = BOT_TOKEN) -> str:
    data_check_string = "\n".join(f"{k}={fields[k]}" for k in sorted(fields))
    secret = hmac.new(b"WebAppData", token.encode(), hashlib.sha256).digest()
    h = hmac.new(secret, data_check_string.encode(), hashlib.sha256).hexdigest()
    return urlencode({**fields, "hash": h})


def _fields(auth_date: int | None = None) -> dict:
    return {
        "user": json.dumps({"id": 100, "first_name": "Павел", "username": "pavel"}),
        "auth_date": str(auth_date if auth_date is not None else int(time.time())),
        "query_id": "AAA",
    }


def test_valid_init_data_passes():
    init_data = _sign(_fields())
    parsed = validate_init_data(init_data, BOT_TOKEN, max_age_seconds=3600)
    assert json.loads(parsed["user"])["id"] == 100


def test_tampered_hash_rejected():
    init_data = _sign(_fields()) + "0"  # corrupt the hash tail
    with pytest.raises(AuthError):
        validate_init_data(init_data, BOT_TOKEN)


def test_forged_with_wrong_token_rejected():
    init_data = _sign(_fields(), token="999:WRONG")
    with pytest.raises(AuthError):
        validate_init_data(init_data, BOT_TOKEN)


def test_expired_init_data_rejected():
    old = int(time.time()) - 10_000
    init_data = _sign(_fields(auth_date=old))
    with pytest.raises(AuthError):
        validate_init_data(init_data, BOT_TOKEN, max_age_seconds=3600)


def test_missing_hash_rejected():
    with pytest.raises(AuthError):
        validate_init_data(urlencode(_fields()), BOT_TOKEN)
