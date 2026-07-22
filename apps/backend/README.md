# Backend (API + Telegram bot)

FastAPI application that hosts the REST API, the aiogram 3 bot (long polling in
LOCAL_MVP, webhook in FULL), the Player Agent WebSocket, the scheduler and the
device watchdog — all in one asyncio process.

## Layout
```
app/
  api/          REST routers + dependencies + serializers
  bot/          aiogram handlers, keyboards, texts, safe RU command parser
  core/         config, logging (secret-redacting), rbac, security, errors, time
  db/           engine/session, declarative base, seed
  models/       SQLAlchemy 2 models (User, Device, Track, Scenario, Schedule, …)
  repositories/ data access
  schemas/      Pydantic request/response models
  services/     business logic (playback, schedule, auth, tracks, scenarios, audit…)
  websocket/    AgentHub (connections + command futures + live state) + WS endpoint
  main.py       app factory + lifespan
  cli.py        seed / scan-music / create-device / list-devices
```

## Run
```bash
make migrate      # FULL/Postgres; LOCAL_MVP creates tables on boot
make seed
make run-backend  # uvicorn app.main:app :8000  (+ bot)
```

## Docs
- OpenAPI: `http://127.0.0.1:8000/docs`
- Health: `GET /health`

## Tests
```bash
pytest apps/backend/tests   # unit + integration (fake agent over the hub)
```
Key coverage: RBAC, Telegram initData validation, command TTL/idempotency, volume
policy, schedule recurrence + conflicts + timezone, file validation/SHA-256,
offline device, reconnect, and the full play→volume→pause→resume→stop flow.
