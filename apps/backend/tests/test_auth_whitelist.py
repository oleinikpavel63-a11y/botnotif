from __future__ import annotations

from app.core.rbac import Role
from app.services.auth import AuthService


async def test_initial_owner_autoprovisioned(session):
    # INITIAL_OWNER_TELEGRAM_ID=100 (see conftest env).
    user = await AuthService(session).resolve_user(100, first_name="Boss")
    assert user is not None
    assert user.role_enum == Role.OWNER


async def test_unknown_user_denied(session):
    user = await AuthService(session).resolve_user(999999, first_name="Stranger")
    assert user is None


async def test_inactive_user_denied(session, operator):
    operator.is_active = False
    await session.commit()
    user = await AuthService(session).resolve_user(operator.telegram_user_id)
    assert user is None


async def test_profile_refreshed_on_resolve(session, operator):
    user = await AuthService(session).resolve_user(
        operator.telegram_user_id, username="new_handle", first_name="Павел"
    )
    assert user is not None
    assert user.username == "new_handle"
    assert user.last_seen_at is not None
