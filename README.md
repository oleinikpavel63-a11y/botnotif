# 🏕 Живая вода • Рупор — Living Water Audio Control

Система удалённого управления музыкой и объявлениями через рупоры (систему
оповещения) христианского лагеря «Живая вода».

Авторизованные сотрудники управляют воспроизведением из **Telegram-бота** и
**Telegram Mini App**. Звук физически воспроизводит **Player Agent** —
отдельная программа на ноутбуке/мини-ПК, подключённом к микшеру/усилителю/рупорам,
через `mpv`.

```
Telegram Bot / Mini App
        │
        ▼
   Backend API (FastAPI + aiogram)
        │  защищённое WebSocket-соединение (исходящее от агента)
        ▼
   Player Agent  ──►  mpv (JSON IPC)  ──►  аудиоустройство  ──►  микшер / усилитель / рупоры
```

Player Agent сам устанавливает **исходящее** соединение с сервером — на ноутбуке
лагеря **не нужно открывать входящие порты**.

---

## Содержание

1. [Что делает проект](#1-что-делает-проект)
2. [Архитектура](#2-архитектура)
3. [Быстрый запуск LOCAL_MVP](#3-быстрый-запуск-local_mvp)
4. [Создание Telegram-бота (BotFather)](#4-создание-telegram-бота-botfather)
5. [Как узнать свой Telegram ID](#5-как-узнать-свой-telegram-id)
6. [Установка mpv](#6-установка-mpv)
7. [Выбор аудиоустройства](#7-выбор-аудиоустройства)
8. [Добавление первой песни](#8-добавление-первой-песни)
9. [Сценарий «Общий сбор»](#9-сценарий-общий-сбор)
10. [Проверка звука](#10-проверка-звука)
11. [Mini App](#11-mini-app)
12. [Production deployment (FULL)](#12-production-deployment-full)
13. [Резервное копирование базы](#13-резервное-копирование-базы)
14. [Troubleshooting](#14-troubleshooting)
15. [Обновление системы](#15-обновление-системы)
16. [Аварийная остановка](#16-аварийная-остановка)
17. [Чек-лист перед сменой лагеря](#17-чек-лист-перед-сменой-лагеря)

---

## 1. Что делает проект

* Включает музыку, сигналы сбора/подъёма/отбоя, приглашения на приём пищи, объявления.
* Управление из Telegram: команды, inline-кнопки, быстрые сценарии, Mini App.
* Работает офлайн: треки заранее синхронизируются на устройство; уже начатое
  воспроизведение продолжается при потере интернета.
* Роли пользователей (OWNER / ADMIN / OPERATOR / VIEWER), whitelist, аудит.
* Расписание с часовым поясом `Europe/Chisinau`.
* Аварийная остановка (кнопка, CLI, stop-файл, горячая клавиша).

## 2. Архитектура

Monorepo:

```
apps/
  backend/       FastAPI + aiogram 3 + SQLAlchemy 2 + Alembic (bot, API, websocket, services)
  player-agent/  WebSocket-клиент + mpv JSON IPC + локальный кэш + CLI
  mini-app/      React + TypeScript + Vite + Telegram Web App SDK
packages/
  shared-contracts/  Канонический протокол команд (Python + TypeScript + JSON)
infra/           docker / nginx / systemd
scripts/         Windows PowerShell + утилиты установки
storage/music/   Локальное хранилище аудио
```

Два режима работы (переключаются через `APP_MODE`):

| | **LOCAL_MVP** | **FULL** |
|---|---|---|
| Запуск | один Windows-ноутбук | VPS + агенты |
| БД | SQLite | PostgreSQL |
| Telegram | long polling | webhook |
| Mini App | опционально | да |
| Агентов / зон | 1 | несколько |

Бизнес-логика одинакова в обоих режимах — переход LOCAL_MVP → FULL не требует
переписывания.

## 3. Быстрый запуск LOCAL_MVP

### Вариант A — через Docker (backend + бот)

```bash
cp .env.example .env
# отредактируйте .env: TELEGRAM_BOT_TOKEN, INITIAL_OWNER_TELEGRAM_ID, AGENT_DEVICE_TOKEN
docker compose --profile local up -d
```

Player Agent запускается **вне Docker** (нужен прямой доступ к звуку):

```bash
cd apps/player-agent
python -m agent.main
```

### Вариант B — всё локально, без Docker (рекомендуется для Windows)

```bash
# 1. Установить зависимости (единый venv для backend + agent + contracts)
make install            # или: bash scripts/install.sh

# 2. Настроить окружение
cp .env.example .env    # заполнить TELEGRAM_BOT_TOKEN, INITIAL_OWNER_TELEGRAM_ID, AGENT_DEVICE_TOKEN

# 3. Применить миграции и засеять стартовые данные
make migrate
make seed

# 4. Запустить backend + бот
make run-backend        # uvicorn на http://127.0.0.1:8000

# 5. В другом терминале — Player Agent
make run-agent
```

После этого напишите боту `/start`.

## 4. Создание Telegram-бота (BotFather)

1. Откройте [@BotFather](https://t.me/BotFather).
2. `/newbot` → задайте имя и username (заканчивается на `bot`).
3. Скопируйте токен вида `123456:ABC-DEF...` → в `.env` как `TELEGRAM_BOT_TOKEN`.
4. (Опционально) `/setcommands` — список команд подставит сам бот при старте.
5. Для Mini App: `/newapp` или `/setmenubutton` → URL вашего Mini App (`MINI_APP_URL`).

## 5. Как узнать свой Telegram ID

* Напишите [@userinfobot](https://t.me/userinfobot) — он ответит числовым ID.
* Впишите его в `.env` как `INITIAL_OWNER_TELEGRAM_ID`. Этот пользователь станет
  OWNER при первом запуске (сидинг).

## 6. Установка mpv

* **Windows:** скачайте сборку с <https://mpv.io/installation/> (например,
  `mpv.io` → Windows builds shinchiro). Распакуйте, укажите путь к `mpv.exe` в
  `.env` → `MPV_EXECUTABLE_PATH` (или добавьте в `PATH`).
* **Linux:** `sudo apt install mpv` (Debian/Ubuntu) / `sudo pacman -S mpv`.
* **macOS:** `brew install mpv`.

Проверка: `mpv --version`.

## 7. Выбор аудиоустройства

```bash
cd apps/player-agent
python -m agent.cli list-audio-devices
```

Скопируйте нужное имя (например, `wasapi/{...}` на Windows, `alsa/...` или
`pulse/...` на Linux) в `.env` → `MPV_AUDIO_DEVICE`. Пустое значение = устройство
по умолчанию ОС.

Тест: `python -m agent.cli test-audio`.

## 8. Добавление первой песни

* **Локальная папка:** положите MP3 в `storage/music/` и выполните
  `make scan-music` (`python -m app.cli scan-music`).
* **Через Telegram:** `/panel` → «➕ Добавить трек» → отправьте боту аудиофайл.
* **Через Mini App:** страница «Музыка» → drag-and-drop.

## 9. Сценарий «Общий сбор»

Стартовые сценарии создаются сидингом (`make seed` или автоматически при первом
запуске backend). «Общий сбор» (`general_gathering`) уже настроен: громкость 65%,
fade-in 2s, требует подтверждения. Привяжите к нему трек:

```bash
cd apps/backend
python -m app.cli list-scenarios                          # посмотреть коды и привязки
python -m app.cli bind-scenario general_gathering "Сбор"  # привязать трек по названию
```

(Также можно привязать трек в Mini App на странице «Сценарии».) Треки без
привязки к сценарию всё равно доступны через `/play` в боте.

## 10. Проверка звука

1. Убедитесь, что Player Agent онлайн: `/devices` в боте покажет 🟢.
2. Нажмите «🏕 Сбор» → подтвердите → звук пойдёт в рупоры.
3. `/now` покажет текущий трек, громкость и кто запустил.

## 11. Mini App

```bash
cd apps/mini-app
npm install
npm run dev        # http://127.0.0.1:5173
```

Для интеграции с Telegram укажите публичный HTTPS-URL Mini App в BotFather
(`/setmenubutton`) и в `.env` → `MINI_APP_URL`. Локально можно проверить через
`?tg-debug` (см. `apps/mini-app/README.md`).

## 12. Production deployment (FULL)

См. `infra/` и раздел `docs/deployment.md`. Кратко:

```bash
# на VPS
cp .env.example .env      # APP_MODE=FULL, DATABASE_URL=postgresql+asyncpg://...
docker compose --profile full up -d
```

* PostgreSQL, Telegram webhook (`PUBLIC_BASE_URL` + `TELEGRAM_WEBHOOK_SECRET`),
  nginx reverse proxy c HTTPS/WSS, статика Mini App.
* Player Agent(ы) на устройствах лагеря подключаются к `wss://<домен>/ws/agent`.

## 13. Резервное копирование базы

* **SQLite:** копируйте `data/app.db` (при остановленном сервисе или через
  `sqlite3 data/app.db ".backup backup.db"`).
* **PostgreSQL:** `pg_dump` — см. `scripts/backup.sh`.

## 14. Troubleshooting

| Симптом | Решение |
|---|---|
| Бот не отвечает | Проверьте `TELEGRAM_BOT_TOKEN`, интернет, логи backend |
| 🔴 Рупор офлайн | Запущен ли Player Agent? Есть ли heartbeat в логах? |
| ⚠️ Трек не синхронизирован | `make scan-music`, дождитесь загрузки на устройство |
| Нет звука | `python -m agent.cli test-audio`, проверьте `MPV_AUDIO_DEVICE` |
| «Команда устарела» | TTL истёк — откройте панель и повторите |

## 15. Обновление системы

```bash
git pull
make install
make migrate
# перезапустите backend и Player Agent
```

## 16. Аварийная остановка

* Bot / Mini App: кнопка «🛑 Аварийный стоп».
* На устройстве: `python -m agent.cli stop` (немедленно, без fade-out).
* Stop-файл: создайте файл, указанный в `AGENT_STOP_FILE` — агент немедленно
  остановит звук даже при потере связи с backend.
* Горячая клавиша (настраивается в конфигурации агента).

После аварийного stop автоматическое возобновление **запрещено**.

## 17. Чек-лист перед сменой лагеря

См. [`docs/camp-start-checklist.md`](docs/camp-start-checklist.md).

---

## Разработка

```bash
make lint          # ruff
make typecheck     # mypy
make test          # pytest (unit + integration, с MockPlayer)
make format        # ruff format
```

Лицензия: используйте только аудио, на воспроизведение которого у вас есть права.
Скачивание с YouTube/Spotify намеренно не реализовано.
