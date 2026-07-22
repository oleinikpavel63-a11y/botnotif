from __future__ import annotations

import pytest
from app.core.errors import ValidationError
from app.core.security import safe_filename
from app.services.tracks import TrackService, sha256_bytes


def test_safe_filename_strips_path_traversal():
    assert safe_filename("../../etc/passwd") == "passwd"
    assert safe_filename("..\\..\\windows\\system32\\evil.dll") == "evil.dll"
    assert safe_filename("/abs/path/song.mp3") == "song.mp3"
    assert safe_filename("...") == "audio"
    assert safe_filename("normal song.mp3").endswith(".mp3")


def test_safe_filename_no_leading_dot():
    assert not safe_filename(".hidden").startswith(".")


async def test_upload_validation_rejects_bad_extension(session):
    svc = TrackService(session)
    with pytest.raises(ValidationError):
        svc.validate_upload("virus.exe", 1000)


async def test_upload_validation_rejects_oversize(session):
    from app.core.config import settings

    svc = TrackService(session)
    with pytest.raises(ValidationError):
        svc.validate_upload("big.mp3", settings.max_upload_bytes + 1)


async def test_create_from_bytes_computes_sha_and_dedups(session, owner):
    svc = TrackService(session)
    data = b"some audio bytes" * 50
    t1 = await svc.create_from_bytes(data, filename="a.mp3", title="A", creator=owner)
    assert t1.sha256 == sha256_bytes(data)
    # Same content -> deduplicated to the same row.
    t2 = await svc.create_from_bytes(data, filename="b.mp3", title="B", creator=owner)
    assert t1.id == t2.id
