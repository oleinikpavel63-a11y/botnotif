from __future__ import annotations

from app.websocket import agent as ws_agent
from app.websocket.hub import hub
from fastapi import WebSocketDisconnect
from lw_contracts import AgentHeartbeat, DeviceState, PlayerState


class FakeWS:
    def __init__(self, incoming: list[dict]) -> None:
        self._incoming = list(incoming)
        self.sent: list[dict] = []
        self.closed = False

    async def accept(self) -> None:
        pass

    async def receive_json(self) -> dict:
        if not self._incoming:
            raise WebSocketDisconnect()
        return self._incoming.pop(0)

    async def send_json(self, data: dict) -> None:
        self.sent.append(data)

    async def close(self) -> None:
        self.closed = True


async def test_agent_auth_success(session, device):
    ws = FakeWS(
        [
            {
                "kind": "auth",
                "device_id": "main-camp-speakers",
                "token": "device-secret-token",
                "app_version": "1.0.0",
            }
        ]
    )
    await ws_agent.agent_ws_endpoint(ws)
    kinds = [m["kind"] for m in ws.sent]
    assert "auth_ok" in kinds


async def test_agent_auth_bad_token_rejected(session, device):
    ws = FakeWS(
        [
            {
                "kind": "auth",
                "device_id": "main-camp-speakers",
                "token": "WRONG",
                "app_version": "1.0.0",
            }
        ]
    )
    await ws_agent.agent_ws_endpoint(ws)
    assert ws.sent and ws.sent[0]["kind"] == "auth_error"
    assert ws.closed


async def test_heartbeat_updates_state_and_db(session, device):
    state = DeviceState(
        device_id="main-camp-speakers",
        player_state=PlayerState.PLAYING,
        volume=70,
        audio_device="USB Audio",
    )
    await ws_agent._handle_message("main-camp-speakers", AgentHeartbeat(state=state))
    assert hub.get_state("main-camp-speakers").volume == 70

    await session.refresh(device)
    assert device.last_seen_at is not None
    assert device.audio_device_name == "USB Audio"
