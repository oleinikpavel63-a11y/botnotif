from __future__ import annotations

import pytest
from app.core.errors import VolumeNotAllowed
from app.core.rbac import Role
from app.services.volume import effective_max, resolve_volume, step_volume


def test_operator_capped_at_safe_volume():
    assert effective_max(Role.OPERATOR, None) == 80
    with pytest.raises(VolumeNotAllowed):
        resolve_volume(90, role=Role.OPERATOR)


def test_admin_high_volume_requires_confirmation():
    decision = resolve_volume(90, role=Role.ADMIN)
    assert decision.volume == 90
    assert decision.requires_high_confirmation is True

    confirmed = resolve_volume(90, role=Role.ADMIN, high_confirmed=True)
    assert confirmed.requires_high_confirmation is False


def test_safe_volume_no_confirmation():
    decision = resolve_volume(65, role=Role.OPERATOR)
    assert decision.requires_high_confirmation is False


def test_negative_clamped_to_zero():
    assert resolve_volume(-5, role=Role.OWNER).volume == 0


def test_step_volume_respects_ceiling():
    # Operator stepping up never exceeds the safe ceiling (80).
    assert step_volume(78, 5, role=Role.OPERATOR) == 80
    assert step_volume(10, -5, role=Role.OPERATOR) == 5
    assert step_volume(0, -5, role=Role.OPERATOR) == 0
