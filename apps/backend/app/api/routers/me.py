from __future__ import annotations

from fastapi import APIRouter

from ...schemas.auth import CurrentUserOut
from ..deps import CurrentUser
from ..serializers import current_user_out

router = APIRouter(tags=["me"])


@router.get("/me", response_model=CurrentUserOut)
async def get_me(user: CurrentUser) -> CurrentUserOut:
    return current_user_out(user)
