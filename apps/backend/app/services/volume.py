"""Volume policy: clamping, safety thresholds, per-role and per-device limits."""

from __future__ import annotations

from dataclasses import dataclass

from ..core.config import settings
from ..core.errors import VolumeNotAllowed
from ..core.rbac import Role
from ..models import Device


@dataclass(frozen=True)
class VolumeDecision:
    volume: int
    requires_high_confirmation: bool


def role_max_volume(role: Role) -> int:
    """OPERATOR is capped at the safe volume; ADMIN/OWNER may go higher."""
    if role in (Role.OWNER, Role.ADMIN):
        return settings.absolute_max_volume
    return settings.max_safe_volume


def device_max_volume(device: Device | None) -> int:
    if device is None:
        return settings.absolute_max_volume
    return min(device.max_volume, settings.absolute_max_volume)


def effective_max(role: Role, device: Device | None) -> int:
    return min(role_max_volume(role), device_max_volume(device))


def resolve_volume(
    requested: int,
    *,
    role: Role,
    device: Device | None = None,
    high_confirmed: bool = False,
) -> VolumeDecision:
    """Validate a requested volume against role/device limits.

    Raises :class:`VolumeNotAllowed` if the request exceeds the caller's ceiling.
    Flags ``requires_high_confirmation`` when above the safe threshold and not yet
    confirmed.
    """
    requested = int(requested)
    if requested < 0:
        requested = 0
    ceiling = effective_max(role, device)
    if requested > ceiling:
        raise VolumeNotAllowed(
            f"Нельзя установить громкость выше {ceiling}%. "
            f"Максимум для вашей роли/устройства: {ceiling}%."
        )
    needs_confirm = requested > settings.max_safe_volume and not high_confirmed
    return VolumeDecision(volume=requested, requires_high_confirmation=needs_confirm)


def step_volume(current: int, delta: int, *, role: Role, device: Device | None = None) -> int:
    """Nudge volume by ``delta`` (e.g. ±5), clamped to policy — never raises."""
    target = max(0, current + delta)
    return min(target, effective_max(role, device))
