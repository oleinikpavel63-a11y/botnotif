"""Role-Based Access Control.

Permissions are always re-checked on the backend. Hiding a button in the UI is
never sufficient — every service entry point that mutates state calls
:func:`require`.
"""

from __future__ import annotations

from enum import Enum

from .errors import PermissionDenied


class Role(str, Enum):
    OWNER = "OWNER"
    ADMIN = "ADMIN"
    OPERATOR = "OPERATOR"
    VIEWER = "VIEWER"


#: Higher number = more powerful. Used for "at least this role" checks.
ROLE_RANK: dict[Role, int] = {
    Role.VIEWER: 10,
    Role.OPERATOR: 20,
    Role.ADMIN: 30,
    Role.OWNER: 40,
}


class Permission(str, Enum):
    # Playback
    PLAYBACK_CONTROL = "playback:control"  # play/pause/resume/stop allowed tracks
    PLAYBACK_VOLUME = "playback:volume"
    PLAYBACK_EMERGENCY = "playback:emergency"
    PLAYBACK_VIEW = "playback:view"
    # Tracks / playlists
    TRACK_MANAGE = "track:manage"
    # Scenarios
    SCENARIO_MANAGE = "scenario:manage"
    # Schedule
    SCHEDULE_MANAGE = "schedule:manage"
    SCHEDULE_VIEW = "schedule:view"
    # Devices
    DEVICE_MANAGE = "device:manage"
    DEVICE_VIEW = "device:view"
    # Users
    USER_VIEW = "user:view"
    USER_MANAGE_OPERATORS = "user:manage_operators"  # add operators
    USER_MANAGE_ADMINS = "user:manage_admins"  # add/remove admins (OWNER only)
    # System
    AUDIT_VIEW = "audit:view"
    SETTINGS_MANAGE = "settings:manage"


_VIEWER: set[Permission] = {
    Permission.PLAYBACK_VIEW,
    Permission.DEVICE_VIEW,
    Permission.SCHEDULE_VIEW,
}
_OPERATOR: set[Permission] = _VIEWER | {
    Permission.PLAYBACK_CONTROL,
    Permission.PLAYBACK_VOLUME,
}
_ADMIN: set[Permission] = _OPERATOR | {
    Permission.TRACK_MANAGE,
    Permission.SCENARIO_MANAGE,
    Permission.SCHEDULE_MANAGE,
    Permission.USER_VIEW,
    Permission.USER_MANAGE_OPERATORS,
    Permission.AUDIT_VIEW,
    Permission.PLAYBACK_EMERGENCY,
}
_OWNER: set[Permission] = _ADMIN | {
    Permission.DEVICE_MANAGE,
    Permission.USER_MANAGE_ADMINS,
    Permission.SETTINGS_MANAGE,
}

ROLE_PERMISSIONS: dict[Role, set[Permission]] = {
    Role.VIEWER: _VIEWER,
    Role.OPERATOR: _OPERATOR,
    Role.ADMIN: _ADMIN,
    Role.OWNER: _OWNER,
}


def has_permission(role: Role, permission: Permission) -> bool:
    return permission in ROLE_PERMISSIONS.get(role, set())


def require(role: Role, permission: Permission) -> None:
    """Raise :class:`PermissionDenied` if ``role`` lacks ``permission``."""
    if not has_permission(role, permission):
        raise PermissionDenied("Недостаточно прав для этого действия.")


def at_least(role: Role, minimum: Role) -> bool:
    return ROLE_RANK[role] >= ROLE_RANK[minimum]
