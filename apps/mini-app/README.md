# Живая вода • Рупор — Telegram Mini App

Admin panel (Telegram Mini App) for the **Living Water Audio Control** system.
React + TypeScript + Vite frontend that talks to the existing FastAPI backend
in `apps/backend`.

Camp-calm aesthetic, mobile-first, one-handed use, light/dark aware, with
haptics, skeleton/empty/error states, confirmation sheets for dangerous
actions, and an accident-protected emergency stop.

## Tech stack

- **React 18 + TypeScript** (strict mode) + **Vite 5**
- **@tanstack/react-query** — server state, caching, polling fallback
- **react-router-dom** (hash router) — routing under the `/app` mount
- **zod** — runtime validation of every API response
- **@twa-dev/sdk** + the official `telegram-web-app.js` bridge — Telegram WebApp
  SDK, with a browser fallback for local development
- **Tailwind CSS** — styling with the canonical palette
- **Playwright** — E2E specs

## Getting started

```bash
cd apps/mini-app
cp .env.example .env        # then edit values
npm install
npm run dev                 # http://127.0.0.1:5173
```

The backend must be running (default `http://127.0.0.1:8000`). Start it from the
repo root (see the top-level README) — typically `make dev` / `uvicorn`.

### Environment variables (`.env`)

| Variable              | Default                  | Purpose                                                   |
| --------------------- | ------------------------ | --------------------------------------------------------- |
| `VITE_API_BASE_URL`   | `http://127.0.0.1:8000`  | Base URL of the FastAPI backend (no trailing slash).      |
| `VITE_DEV_INIT_DATA`  | _(empty)_                | Raw Telegram `initData` used for browser-dev auth.        |

## Scripts

| Command             | What it does                                              |
| ------------------- | -------------------------------------------------------- |
| `npm run dev`       | Start the Vite dev server.                                |
| `npm run build`     | Type-check (`tsc -b`) then produce a production build.    |
| `npm run preview`   | Preview the production build locally.                     |
| `npm run typecheck` | Type-check only.                                          |
| `npm run lint`      | ESLint (zero warnings allowed).                           |
| `npm run test:e2e`  | Run the Playwright E2E specs.                             |

## Authentication flow

1. On load the app resolves a raw Telegram `initData` string.
   **Precedence:** `?initData=…` query param → real Telegram `WebApp.initData`
   → `VITE_DEV_INIT_DATA`.
2. It `POST`s `{ init_data }` to `/api/auth/telegram` and receives an
   `access_token` + the current user.
3. The token is kept in memory and mirrored to `sessionStorage`, and sent as
   `Authorization: Bearer <token>` on every request.
4. Roles (`OWNER | ADMIN | OPERATOR | VIEWER`) gate the UI **for convenience
   only** — the backend re-checks every mutation.

### Browser-dev fallback (no Telegram)

Open the app outside Telegram in one of two ways:

- Append a real `initData` string to the URL:
  `http://127.0.0.1:5173/?initData=<raw-init-data>`
- Or set `VITE_DEV_INIT_DATA=<raw-init-data>` in `.env`.

The Login screen also has a field to paste `initData` directly.

To obtain a valid `initData` for dev, open your bot's Mini App in Telegram once
and copy `window.Telegram.WebApp.initData`, or generate a signed test string
with your bot token.

## Live updates (SSE)

The app subscribes to `GET /api/admin/events?token=<access_token>` via
`EventSource`. Incoming `device_state` / `command_update` / `sync_status`
frames patch the react-query cache in place. If SSE cannot connect, the app
transparently falls back to polling (every ~4s). The header shows a **Live**
vs **Опрос** (polling) indicator.

## Screens

| Route        | Screen               | Notes                                                    |
| ------------ | -------------------- | -------------------------------------------------------- |
| `/`          | Главная (Home)       | Device card, now-playing, quick scenarios, volume, stop. |
| `/music`     | Музыка (Music)       | Track list + drag-and-drop upload (admin).               |
| `/scenarios` | Сценарии (Scenarios) | List + create/edit (admin).                              |
| `/schedule`  | Расписание (Schedule)| List + create; enable/disable; delete (admin).           |
| `/devices`   | Устройства (Devices) | Live state + per-track sync badges.                      |
| `/users`     | Пользователи (Users) | ADMIN/OWNER only (OPERATOR is blocked + redirected).     |
| `/audit`     | Журнал (Audit)       | Recent actions (ADMIN/OWNER).                            |
| `/settings`  | Настройки (Settings) | System status, mode, timezone, profile.                  |

## Volume & safety

- ±5% steppers and a slider.
- Crossing the **safe threshold (80%)** triggers a high-volume confirmation
  sheet; on confirm the request is re-sent with `confirm_high: true`. The
  backend `409 high_volume_confirmation_required` is also handled as a safety
  net.
- **Emergency stop** requires a 1.5s press-and-hold (pointer) or a
  hold-to-confirm sheet (keyboard) before firing
  `POST /stop?immediate=true&emergency=true`.

## Deploying & pointing BotFather at it

1. Build: `npm run build` → outputs to `apps/mini-app/dist`.
2. The FastAPI backend auto-serves the build at `/app` when
   `MINI_APP_ENABLED=true` and `dist/` exists (see `apps/backend/app/main.py`),
   so `https://<your-domain>/app` serves the Mini App. Otherwise host `dist/`
   on any static host (Netlify, Nginx, …).
3. In **@BotFather**:
   - `/setmenubutton` → choose your bot → send the Mini App URL
     (`https://<your-domain>/app`) and a button label (e.g. «Открыть панель»).
   - Or `/newapp` to register a full Mini App and set its URL.
4. Ensure the backend `CORS_ORIGINS` includes your dev origin
   (`http://127.0.0.1:5173`) for local development.

## E2E tests

```bash
npm run test:e2e
```

The specs (`tests/`) mock the backend with `page.route`, so they run fully
offline. They cover: panel open, offline display, run-scenario-with-confirm,
volume change, stop, and OPERATOR being unable to reach the Users screen.

In this repo's CI sandbox, Playwright's Chromium is vendored under
`/opt/pw-browsers`. `playwright.config.ts` points `executablePath` at it and you
should set `PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD=1`. Locally, instead run
`npx playwright install chromium` once and remove/ignore `executablePath`
(override with `PLAYWRIGHT_CHROMIUM_PATH`).

## Project structure

```
src/
  main.tsx App.tsx router.tsx index.css
  lib/        api client, telegram wrapper, sse, queryClient, token, config, format, roles, upload
  types/      contracts.ts (mirror) + schemas.ts (zod)
  hooks/      useAuth, useDevices, useNowPlaying, usePlayback, useScenarios,
              useTracks, useSchedules, useUsers, useAudit, useSystemStatus,
              useSSE, useHaptics, useTheme, useToast, useConfirm
  components/ DeviceCard, NowPlaying, QuickActions, VolumeControl,
              EmergencyStopButton, ConfirmSheet, Sheet, BottomNav, StatusBadge,
              SyncBadge, Skeleton, EmptyState, ErrorState, RoleGate, RequireRole,
              TrackUploader, TrackEditSheet, ScenarioEditSheet, ScheduleForm,
              ToastContainer, ProgressBar, PageTitle, Layout, ui, icons
  pages/      Home, Music, Scenarios, Schedule, Devices, Users, Audit, Settings, Login
tests/        Playwright specs + mocks
```

## Contracts

Types mirror `packages/shared-contracts/typescript/contracts.ts` (plus the
list-endpoint fields the backend serializers add). Keep `src/types/contracts.ts`
and `src/types/schemas.ts` in sync with the backend if the API changes.
