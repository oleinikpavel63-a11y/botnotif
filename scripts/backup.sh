#!/usr/bin/env bash
# Back up the database (SQLite for LOCAL_MVP, PostgreSQL for FULL).
# Usage: scripts/backup.sh [output_dir]
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
OUT="${1:-$ROOT/backups}"
mkdir -p "$OUT"
STAMP="$(date +%Y%m%d-%H%M%S)"

# Load DATABASE_URL from .env if present.
if [ -f .env ]; then
    # shellcheck disable=SC1091
    set -a; . ./.env; set +a
fi
DB_URL="${DATABASE_URL:-sqlite+aiosqlite:///./data/app.db}"

case "$DB_URL" in
    sqlite*)
        SRC="${DB_URL##*:///}"
        SRC="${SRC#./}"
        [ -f "$SRC" ] || SRC="data/app.db"
        DEST="$OUT/app-$STAMP.db"
        echo "==> SQLite backup: $SRC -> $DEST"
        if command -v sqlite3 >/dev/null 2>&1; then
            sqlite3 "$SRC" ".backup '$DEST'"
        else
            cp "$SRC" "$DEST"
        fi
        ;;
    postgresql*)
        DEST="$OUT/pg-$STAMP.sql.gz"
        echo "==> PostgreSQL backup -> $DEST"
        # Convert SQLAlchemy URL to libpq form for pg_dump.
        PG_URL="$(echo "$DB_URL" | sed -E 's#\+asyncpg##; s#\+psycopg2##')"
        pg_dump "$PG_URL" | gzip > "$DEST"
        ;;
    *)
        echo "Unknown DATABASE_URL scheme: $DB_URL" >&2
        exit 1
        ;;
esac

echo "==> Backup complete."
# Keep the 30 most recent backups.
ls -1t "$OUT"/* 2>/dev/null | tail -n +31 | xargs -r rm -f
