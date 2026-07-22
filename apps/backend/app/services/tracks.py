from __future__ import annotations

import hashlib
import shutil
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession

from ..core.config import settings
from ..core.errors import ValidationError
from ..core.security import safe_filename
from ..models import Track, User
from ..repositories import TrackRepository
from .audit import AuditService

#: extension -> mime type
ALLOWED_AUDIO: dict[str, str] = {
    ".mp3": "audio/mpeg",
    ".m4a": "audio/mp4",
    ".aac": "audio/aac",
    ".wav": "audio/wav",
    ".ogg": "audio/ogg",
    ".oga": "audio/ogg",
    ".flac": "audio/flac",
}


def sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _extract_duration(path: Path) -> float | None:
    try:
        from mutagen import File as MutagenFile  # local import, optional at runtime

        audio = MutagenFile(str(path))
        if audio is not None and audio.info is not None:
            return float(audio.info.length)
    except Exception:  # pragma: no cover - metadata best-effort
        return None
    return None


class TrackService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repo = TrackRepository(session)
        self.audit = AuditService(session)

    async def list_all(self) -> list[Track]:
        return await self.repo.list_all()

    def validate_upload(self, filename: str, size: int) -> str:
        ext = Path(filename).suffix.lower()
        if ext not in ALLOWED_AUDIO:
            raise ValidationError(
                f"Формат {ext or '?'} не поддерживается. "
                f"Разрешено: {', '.join(sorted(ALLOWED_AUDIO))}."
            )
        if size > settings.max_upload_bytes:
            raise ValidationError(
                f"Файл слишком большой ({size // (1024 * 1024)} МБ). "
                f"Максимум {settings.max_upload_size_mb} МБ."
            )
        return ext

    def _target_path(self, filename: str, sha256: str) -> Path:
        settings.music_dir.mkdir(parents=True, exist_ok=True)
        base = safe_filename(filename)
        # Prefix with a short hash slice to avoid collisions but keep readability.
        return settings.music_dir / f"{sha256[:8]}_{base}"

    async def create_from_bytes(
        self,
        data: bytes,
        *,
        filename: str,
        title: str | None = None,
        category: str | None = None,
        creator: User | None = None,
        telegram_file_id: str | None = None,
        telegram_file_unique_id: str | None = None,
        recommended_volume: int | None = None,
        is_announcement: bool = False,
        interface: str = "bot",
    ) -> Track:
        ext = self.validate_upload(filename, len(data))
        sha = sha256_bytes(data)

        existing = await self.repo.get_by_sha256(sha)
        if existing is not None:
            return existing

        target = self._target_path(filename, sha)
        target.write_bytes(data)
        duration = _extract_duration(target)

        return await self._persist(
            title=title or Path(filename).stem,
            filename=filename,
            ext=ext,
            sha=sha,
            size=len(data),
            path=target,
            duration=duration,
            category=category,
            creator=creator,
            telegram_file_id=telegram_file_id,
            telegram_file_unique_id=telegram_file_unique_id,
            recommended_volume=recommended_volume,
            is_announcement=is_announcement,
            interface=interface,
        )

    async def import_local_file(self, source: Path, *, creator: User | None = None) -> Track | None:
        ext = source.suffix.lower()
        if ext not in ALLOWED_AUDIO:
            return None
        sha = sha256_of(source)
        existing = await self.repo.get_by_sha256(sha)
        if existing is not None:
            return existing
        target = self._target_path(source.name, sha)
        if source.resolve() != target.resolve():
            shutil.copy2(source, target)
        duration = _extract_duration(target)
        return await self._persist(
            title=source.stem,
            filename=source.name,
            ext=ext,
            sha=sha,
            size=target.stat().st_size,
            path=target,
            duration=duration,
            category="imported",
            creator=creator,
            interface="cli",
        )

    async def scan_music_folder(self, *, creator: User | None = None) -> list[Track]:
        imported: list[Track] = []
        folder = settings.music_dir
        folder.mkdir(parents=True, exist_ok=True)
        for path in sorted(folder.iterdir()):
            if path.is_file() and path.suffix.lower() in ALLOWED_AUDIO:
                track = await self.import_local_file(path, creator=creator)
                if track is not None:
                    imported.append(track)
        return imported

    async def delete(self, actor: User, track_id, *, interface: str = "api") -> None:
        track = await self.repo.get_or_404(track_id)
        await self.repo.delete(track)
        await self.audit.log(
            action="track.delete",
            user=actor,
            entity_type="track",
            entity_id=str(track_id),
            interface=interface,
            meta={"title": track.title},
        )

    async def _persist(self, **kw) -> Track:
        track = Track(
            title=kw["title"],
            category=kw.get("category"),
            original_filename=kw["filename"],
            mime_type=ALLOWED_AUDIO[kw["ext"]],
            duration=kw.get("duration"),
            size=kw["size"],
            sha256=kw["sha"],
            storage_path=str(kw["path"]),
            telegram_file_id=kw.get("telegram_file_id"),
            telegram_file_unique_id=kw.get("telegram_file_unique_id"),
            recommended_volume=kw.get("recommended_volume") or settings.default_volume,
            is_announcement=kw.get("is_announcement", False),
            created_by=kw["creator"].id if kw.get("creator") else None,
        )
        self.repo.add(track)
        await self.repo.flush()
        await self.audit.log(
            action="track.add",
            user=kw.get("creator"),
            entity_type="track",
            entity_id=str(track.id),
            interface=kw.get("interface"),
            meta={"title": track.title, "sha256": track.sha256},
        )
        return track
