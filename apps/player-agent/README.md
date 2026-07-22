# Player Agent

Runs on the computer physically wired to the camp sound system. Dials **out** to
the backend over WSS (no inbound ports), drives `mpv` via JSON IPC, and keeps a
verified local cache of tracks so playback survives an internet outage.

## Responsibilities
- Authenticate with the device token, send heartbeats, auto-reconnect.
- Execute `PLAY / PAUSE / RESUME / STOP / SET_VOLUME` with fade-in/out.
- Enforce **command TTL** and **idempotency** (never replay an old PLAY/STOP).
- Download + **SHA-256-verify** files before playing; refuse unverified files.
- Emergency stop via CLI / stop-file, even with no backend connection.
- Never auto-resume after restart (`RESUME_AFTER_RESTART=false`).

## Quick start
```bash
# from repo root (single venv installs everything)
make install
# edit .env: AGENT_SERVER_URL, AGENT_DEVICE_ID, AGENT_DEVICE_TOKEN, MPV_AUDIO_DEVICE
python -m agent.main            # or: make run-agent
```

## CLI
```bash
python -m agent.cli list-audio-devices   # pick MPV_AUDIO_DEVICE
python -m agent.cli test-audio           # play a 2s test tone
python -m agent.cli status               # local status
python -m agent.cli stop                 # EMERGENCY stop (writes stop-file)
```

## Audio device selection
`MPV_AUDIO_DEVICE` values come from `list-audio-devices`:
- Windows: `wasapi/{...}`
- Linux (ALSA): `alsa/plughw:CARD=...`
- Linux (PulseAudio/PipeWire): `pulse/<sink>`

Empty = OS default device.

## Platforms
- Windows 10/11 — see `scripts/windows/` and `docs/windows-setup.md`.
- Linux / Raspberry Pi — see `infra/systemd/living-water-player-agent.service`.

## Tests
```bash
pytest apps/player-agent/tests      # uses MockPlayer — no real audio needed
```
