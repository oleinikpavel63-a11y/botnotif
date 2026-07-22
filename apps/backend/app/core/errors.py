"""Domain-level exceptions with user-friendly (Russian) messages.

The API and bot translate these into clean messages — never a raw traceback.
"""

from __future__ import annotations


class DomainError(Exception):
    """Base class for expected, user-facing errors."""

    #: HTTP status the API should return.
    status_code: int = 400
    #: Short machine code.
    code: str = "domain_error"

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class PermissionDenied(DomainError):
    status_code = 403
    code = "permission_denied"


class NotFound(DomainError):
    status_code = 404
    code = "not_found"


class ValidationError(DomainError):
    status_code = 422
    code = "validation_error"


class DeviceOffline(DomainError):
    status_code = 409
    code = "device_offline"


class CommandExpired(DomainError):
    status_code = 410
    code = "command_expired"


class TrackNotSynced(DomainError):
    status_code = 409
    code = "track_not_synced"


class VolumeNotAllowed(DomainError):
    status_code = 403
    code = "volume_not_allowed"


class HighVolumeConfirmationRequired(DomainError):
    status_code = 409
    code = "high_volume_confirmation_required"


class PlaybackFailed(DomainError):
    status_code = 409
    code = "playback_failed"


class AuthError(DomainError):
    status_code = 401
    code = "auth_error"


class Conflict(DomainError):
    status_code = 409
    code = "conflict"
