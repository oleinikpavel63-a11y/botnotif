from __future__ import annotations

import pytest
from app.core.errors import PermissionDenied
from app.core.rbac import Permission, Role, at_least, has_permission, require


def test_owner_has_everything():
    for perm in Permission:
        assert has_permission(Role.OWNER, perm)


def test_operator_can_control_but_not_manage():
    assert has_permission(Role.OPERATOR, Permission.PLAYBACK_CONTROL)
    assert has_permission(Role.OPERATOR, Permission.PLAYBACK_VOLUME)
    assert not has_permission(Role.OPERATOR, Permission.TRACK_MANAGE)
    assert not has_permission(Role.OPERATOR, Permission.USER_MANAGE_OPERATORS)
    assert not has_permission(Role.OPERATOR, Permission.DEVICE_MANAGE)


def test_viewer_is_read_only():
    assert has_permission(Role.VIEWER, Permission.PLAYBACK_VIEW)
    assert not has_permission(Role.VIEWER, Permission.PLAYBACK_CONTROL)
    assert not has_permission(Role.VIEWER, Permission.PLAYBACK_VOLUME)


def test_admin_cannot_manage_admins_only_owner_can():
    assert not has_permission(Role.ADMIN, Permission.USER_MANAGE_ADMINS)
    assert has_permission(Role.OWNER, Permission.USER_MANAGE_ADMINS)
    assert has_permission(Role.ADMIN, Permission.USER_MANAGE_OPERATORS)


def test_require_raises_for_missing_permission():
    with pytest.raises(PermissionDenied):
        require(Role.VIEWER, Permission.PLAYBACK_CONTROL)
    require(Role.OPERATOR, Permission.PLAYBACK_CONTROL)  # no raise


def test_role_ranking():
    assert at_least(Role.OWNER, Role.OPERATOR)
    assert at_least(Role.OPERATOR, Role.OPERATOR)
    assert not at_least(Role.VIEWER, Role.OPERATOR)
