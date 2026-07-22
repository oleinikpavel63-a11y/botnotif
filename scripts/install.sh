#!/usr/bin/env bash
# Install a single virtualenv with backend + player-agent + shared-contracts.
# Works on Linux / macOS / Raspberry Pi. For Windows use scripts/windows/install.ps1.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

PY="${PYTHON:-python3}"
VENV="${VENV:-.venv}"

echo "==> Creating virtualenv at $VENV"
"$PY" -m venv "$VENV"

PIP="$VENV/bin/pip"
if command -v uv >/dev/null 2>&1; then
    echo "==> Installing with uv"
    uv pip install --python "$VENV/bin/python" -U pip
    uv pip install --python "$VENV/bin/python" -e ./packages/shared-contracts/python
    uv pip install --python "$VENV/bin/python" -e "./apps/backend[dev]"
    uv pip install --python "$VENV/bin/python" -e "./apps/player-agent[dev]"
else
    echo "==> Installing with pip"
    "$PIP" install -U pip
    "$PIP" install -e ./packages/shared-contracts/python
    "$PIP" install -e "./apps/backend[dev]"
    "$PIP" install -e "./apps/player-agent[dev]"
fi

if [ ! -f .env ]; then
    cp .env.example .env
    echo "==> Created .env from .env.example — edit it before starting."
fi

echo "==> Done. Next:"
echo "   1. Edit .env (TELEGRAM_BOT_TOKEN, INITIAL_OWNER_TELEGRAM_ID, AGENT_DEVICE_TOKEN)"
echo "   2. $VENV/bin/python -m app.cli seed        (from apps/backend, or: make seed)"
echo "   3. make run-backend    # start backend + bot"
echo "   4. make run-agent      # start Player Agent (needs mpv)"
