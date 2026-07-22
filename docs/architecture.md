# Architecture

## Components

```
┌──────────────────┐     ┌──────────────────┐
│  Telegram Bot    │     │  Telegram Mini    │
│  (aiogram 3)     │     │  App (React/TS)   │
└────────┬─────────┘     └─────────┬─────────┘
         │ long polling / webhook   │ HTTPS + initData
         ▼                          ▼
      ┌──────────────────────────────────────┐
      │            Backend (FastAPI)          │
      │  ┌────────────────────────────────┐   │
      │  │ transport: REST API + Bot + WS │   │
      │  ├────────────────────────────────┤   │
      │  │ application: services          │   │  RBAC, volume policy,
      │  │  playback / schedule / auth /  │   │  command TTL, idempotency,
      │  │  tracks / scenarios / audit    │   │  confirmation, audit
      │  ├────────────────────────────────┤   │
      │  │ domain: models + repositories  │   │
      │  └────────────────────────────────┘   │
      │   AgentHub (in-memory): connections,  │
      │   command futures, live device state  │
      └───────────────┬───────────────────────┘
                      │ WSS (agent dials OUT — no inbound ports on camp device)
                      ▼
             ┌───────────────────┐
             │   Player Agent    │  heartbeat, reconnect, TTL,
             │   (Python)        │  idempotency, SHA-256 cache,
             │                   │  emergency stop-file
             └─────────┬─────────┘
                       │ JSON IPC
                       ▼
                     ┌─────┐
                     │ mpv │ → audio device → mixer/amp → рупоры
                     └─────┘
```

## Command lifecycle

```
Bot/API → PlaybackService (RBAC + volume + offline checks)
        → create PlaybackCommand (command_id, expires_at) → commit
        → AgentHub.send(ServerCommand) over WS
        → await in-memory future (≤ TTL)
Agent   → RECEIVED → (TTL/idempotency check) → ACCEPTED
        → ensure file (download + SHA-256 verify) → play via mpv
        → STARTED / COMPLETED / FAILED / REJECTED / EXPIRED
Backend → WS handler updates DB + resolves the future
        → Bot edits the status message; API returns CommandResult
```

Guarantees:
- **TTL** — immediate commands carry `expires_at`; expired ones return `EXPIRED`.
- **Idempotency** — the agent persists processed `command_id`s; a command runs at
  most once, even across reconnects (no PLAY/STOP replay).
- **Offline-safe** — a command to a disconnected device is rejected immediately,
  never queued forever. Playback already in progress continues if the network drops.
- **File integrity** — the agent never plays a file whose SHA-256 doesn't match.

## Modes

| | LOCAL_MVP | FULL |
|---|---|---|
| DB | SQLite (`create_all` on boot) | PostgreSQL (Alembic) |
| Telegram | long polling | webhook + secret |
| Front | bot (Mini App optional) | bot + Mini App via nginx |
| Agents/zones | 1 | many |

The service/domain layers are identical across modes — only configuration and the
transport edges change.

## Shared contracts

`packages/shared-contracts` is the single source of truth for the agent↔server
protocol: Pydantic models (Python, runtime-validated), a TypeScript mirror for the
Mini App, and a language-neutral `protocol.json`.
