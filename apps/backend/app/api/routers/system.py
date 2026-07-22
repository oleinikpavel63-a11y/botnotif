from __future__ import annotations

from fastapi import APIRouter

from ...core.config import settings
from ...services.status import StatusService
from ..deps import CurrentUser, SessionDep

router = APIRouter(tags=["system"])


@router.get("/system/status")
async def system_status(session: SessionDep, _: CurrentUser) -> dict:
    status = await StatusService(session).system_status()
    return {
        "app_mode": settings.app_mode.value,
        "timezone": settings.app_timezone,
        "tts_enabled": settings.tts_enabled,
        "mini_app_enabled": settings.mini_app_enabled,
        **status,
    }
