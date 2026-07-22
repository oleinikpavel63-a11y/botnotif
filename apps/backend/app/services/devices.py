from __future__ import annotations

from lw_contracts import DeviceState, DeviceStatus
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.security import generate_device_token, hash_token
from ..core.time import utcnow
from ..models import Device
from ..repositories import DeviceRepository
from ..websocket.hub import hub


class DeviceService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repo = DeviceRepository(session)

    async def get_by_code(self, code: str) -> Device | None:
        return await self.repo.get_by_code(code)

    async def list(self) -> list[Device]:
        return await self.repo.list_all()

    async def create(
        self,
        *,
        code: str,
        name: str,
        zone: str = "Весь лагерь",
        raw_token: str | None = None,
        default_volume: int = 60,
        max_volume: int = 80,
    ) -> tuple[Device, str]:
        """Create a device, returning it and the *raw* token (shown once)."""
        token = raw_token or generate_device_token()
        device = Device(
            code=code,
            name=name,
            zone=zone,
            token_hash=hash_token(token),
            default_volume=default_volume,
            max_volume=max_volume,
            status=DeviceStatus.OFFLINE.value,
        )
        self.repo.add(device)
        await self.repo.flush()
        return device, token

    def is_online(self, device: Device) -> bool:
        if device.status == DeviceStatus.MAINTENANCE.value:
            return False
        return hub.is_online(device.code)

    def live_state(self, device: Device) -> DeviceState | None:
        return hub.get_state(device.code)

    def status_of(self, device: Device) -> DeviceStatus:
        if device.status == DeviceStatus.MAINTENANCE.value:
            return DeviceStatus.MAINTENANCE
        if hub.is_online(device.code):
            state = hub.get_state(device.code)
            if state and state.last_error:
                return DeviceStatus.ERROR
            return DeviceStatus.ONLINE
        return DeviceStatus.OFFLINE

    async def mark_online(
        self, device: Device, *, app_version: str | None, audio_device: str | None
    ) -> None:
        device.status = DeviceStatus.ONLINE.value
        device.last_seen_at = utcnow()
        if app_version:
            device.app_version = app_version
        if audio_device:
            device.audio_device_name = audio_device

    async def heartbeat(self, device: Device, state: DeviceState) -> None:
        device.last_seen_at = utcnow()
        if device.status not in (DeviceStatus.MAINTENANCE.value,):
            device.status = (
                DeviceStatus.ERROR.value if state.last_error else DeviceStatus.ONLINE.value
            )
        if state.audio_device:
            device.audio_device_name = state.audio_device
        if state.app_version:
            device.app_version = state.app_version

    async def mark_offline(self, code: str) -> None:
        device = await self.repo.get_by_code(code)
        if device and device.status not in (
            DeviceStatus.OFFLINE.value,
            DeviceStatus.MAINTENANCE.value,
        ):
            device.status = DeviceStatus.OFFLINE.value

    async def get_default_device(self) -> Device | None:
        """The single device used by LOCAL_MVP quick actions."""
        devices = await self.repo.list_active()
        return devices[0] if devices else None
