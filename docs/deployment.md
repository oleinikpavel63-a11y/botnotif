# Production deployment (FULL mode)

This guide deploys the backend + Mini App on a VPS with PostgreSQL, HTTPS/WSS and
Telegram webhook. Player Agents run on the camp devices and dial out to the VPS.

## 1. Prerequisites

- A VPS (2 vCPU / 2 GB RAM is plenty) with Docker + Docker Compose.
- A domain, e.g. `camp.example.org`, pointing at the VPS.
- TLS certificates (use a load balancer, Caddy, or add certbot to nginx).
- A Telegram bot token (BotFather) and your Telegram user id.

## 2. Configure

```bash
git clone <repo> living-water && cd living-water
cp .env.example .env
```

Edit `.env`:

```ini
APP_ENV=production
APP_MODE=FULL
APP_TIMEZONE=Europe/Chisinau
LOG_JSON=true

TELEGRAM_BOT_TOKEN=<from BotFather>
TELEGRAM_USE_WEBHOOK=true
TELEGRAM_WEBHOOK_SECRET=<random 32+ chars>
INITIAL_OWNER_TELEGRAM_ID=<your id>

DATABASE_URL=postgresql+asyncpg://lwuser:<strong-pass>@postgres:5432/livingwater
POSTGRES_USER=lwuser
POSTGRES_PASSWORD=<strong-pass>
POSTGRES_DB=livingwater

PUBLIC_BASE_URL=https://camp.example.org
MINI_APP_URL=https://camp.example.org/app
CORS_ORIGINS=https://camp.example.org
SECRET_KEY=<random 40+ chars>

AGENT_DEVICE_ID=main-camp-speakers
AGENT_DEVICE_TOKEN=<random per-device secret>
```

> Never commit `.env`. Secrets (bot token, device tokens, DB password, SECRET_KEY,
> webhook secret) stay out of git.

## 3. Launch

```bash
docker compose --profile full up -d --build
docker compose ps          # backend healthy, postgres healthy, web up
docker compose logs -f backend
```

The backend entrypoint runs Alembic migrations (retrying until Postgres is ready)
and seeds the OWNER, default device and scenarios.

## 4. TLS / webhook

Terminate TLS in front of the `web` (nginx) container (load balancer or Caddy).
Telegram requires HTTPS for the webhook — on startup the backend calls
`setWebhook` to `PUBLIC_BASE_URL/telegram/webhook` with the secret token. Verify:

```bash
curl -s "https://api.telegram.org/bot<token>/getWebhookInfo"
```

Set the Mini App URL in BotFather (`/setmenubutton` → `https://camp.example.org/app`).

## 5. Register camp devices

Each Player Agent authenticates with a device token. Create additional devices:

```bash
docker compose exec backend python -m app.cli create-device zone-2-speakers "Столовая"
# prints the token once — put it in that device's .env as AGENT_DEVICE_TOKEN
```

On each camp device (Windows/Linux) set:

```ini
AGENT_SERVER_URL=wss://camp.example.org/ws/agent
AGENT_API_BASE_URL=https://camp.example.org
AGENT_DEVICE_ID=zone-2-speakers
AGENT_DEVICE_TOKEN=<token from create-device>
```

## 6. Backups & monitoring

```bash
# Postgres backup (cron nightly)
scripts/backup.sh /var/backups/living-water
```

- Health endpoint: `GET /health`.
- Container healthchecks are built in (`docker compose ps`).
- Logs are JSON (`LOG_JSON=true`) — ship to your log stack; secrets are redacted.

## 7. Updating

```bash
git pull
docker compose --profile full up -d --build   # entrypoint re-runs migrations
```

## 8. Scaling to more zones

Add a `Device` per zone (`create-device`), run one Player Agent per physical
device, and target zones from scenarios/schedules. The backend already supports
multiple agents and zones — no code changes needed.
