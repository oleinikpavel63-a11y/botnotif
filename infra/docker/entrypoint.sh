#!/usr/bin/env sh
# Backend container entrypoint.
# FULL mode runs Alembic migrations (retrying until the DB is reachable);
# LOCAL_MVP creates tables on startup and just launches uvicorn.
set -eu

cd /app/apps/backend

if [ "${APP_MODE:-LOCAL_MVP}" = "FULL" ]; then
    echo "[entrypoint] FULL mode — running migrations..."
    i=0
    until python -m alembic upgrade head; do
        i=$((i + 1))
        if [ "$i" -ge 20 ]; then
            echo "[entrypoint] migrations failed after $i attempts" >&2
            exit 1
        fi
        echo "[entrypoint] DB not ready, retry $i/20 in 3s..."
        sleep 3
    done
    echo "[entrypoint] seeding..."
    python -m app.cli seed || true
fi

exec python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
