#!/usr/bin/env bash
# One-shot free setup for LOCAL_MVP (Linux / macOS / Raspberry Pi).
# Windows: use scripts\windows\install.ps1 then start.ps1.
#
#   bash scripts/quickstart.sh
#
# Does: venv install -> .env check -> DB + seed -> import music -> next steps.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

green() { printf '\033[32m%s\033[0m\n' "$1"; }
yellow() { printf '\033[33m%s\033[0m\n' "$1"; }
red() { printf '\033[31m%s\033[0m\n' "$1"; }

green "==> 1/5  Проверка окружения"
command -v python3 >/dev/null || { red "Нужен Python 3.11+"; exit 1; }
command -v mpv >/dev/null || yellow "⚠️  mpv не найден — звук не заиграет. Установите mpv (см. README §6) или задайте MPV_EXECUTABLE_PATH в .env."

green "==> 2/5  Установка зависимостей (единый venv)"
if [ ! -x ".venv/bin/python" ]; then
    bash scripts/install.sh
else
    yellow "venv уже существует — пропускаю установку."
fi

green "==> 3/5  Проверка .env"
[ -f .env ] || cp .env.example .env
missing=0
check() {
    local key="$1"
    local val
    val="$(grep -E "^${key}=" .env | head -1 | cut -d= -f2- || true)"
    if [ -z "$val" ]; then
        red "   ✗ $key не заполнен в .env"
        missing=1
    else
        green "   ✓ $key"
    fi
}
check TELEGRAM_BOT_TOKEN
check INITIAL_OWNER_TELEGRAM_ID
check AGENT_DEVICE_TOKEN
if [ "$missing" = "1" ]; then
    echo
    yellow "Заполните недостающие значения в файле .env и запустите скрипт снова:"
    echo "   TELEGRAM_BOT_TOKEN        — от @BotFather"
    echo "   INITIAL_OWNER_TELEGRAM_ID — ваш ID от @userinfobot"
    echo "   AGENT_DEVICE_TOKEN        — любой секрет (например: $(python3 -c 'import secrets;print(secrets.token_urlsafe(24))'))"
    exit 1
fi

green "==> 4/5  База данных, сидинг, импорт музыки"
( cd apps/backend && ../../.venv/bin/python -m app.cli seed )
( cd apps/backend && ../../.venv/bin/python -m app.cli scan-music )

green "==> 5/5  Готово!"
echo
green "Осталось запустить в ДВУХ терминалах:"
echo "   Терминал 1:  make run-backend      # бот + API"
echo "   Терминал 2:  make run-agent        # звук (нужен mpv)"
echo
echo "Затем в Telegram напишите боту /start."
echo "Привязать трек к кнопке «Сбор»:"
echo "   cd apps/backend && ../../.venv/bin/python -m app.cli bind-scenario general_gathering \"название\""
echo
yellow "Хотите открывать панель Mini App с телефона бесплатно?  ->  bash scripts/free-tunnel.sh"
