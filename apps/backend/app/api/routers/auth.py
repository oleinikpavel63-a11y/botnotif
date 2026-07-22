from __future__ import annotations

from fastapi import APIRouter

from ...core.config import settings
from ...core.security import create_access_token
from ...schemas import AuthResponse, TelegramAuthRequest
from ...services.auth import AuthService
from ..deps import SessionDep
from ..serializers import current_user_out

router = APIRouter(tags=["auth"])


@router.post("/auth/telegram", response_model=AuthResponse)
async def auth_telegram(payload: TelegramAuthRequest, session: SessionDep) -> AuthResponse:
    """Validate Telegram Mini App initData and return a short-lived session token."""
    user = await AuthService(session).authenticate_init_data(payload.init_data)
    token = create_access_token(user.telegram_user_id, user.role)
    return AuthResponse(
        access_token=token,
        expires_in=settings.access_token_ttl_seconds,
        user=current_user_out(user),
    )
