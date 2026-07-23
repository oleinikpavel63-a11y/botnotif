#!/usr/bin/env bash
# Free public HTTPS URL for the Mini App / webhook via Cloudflare Tunnel.
# No account, no domain, no VPS. The backend must already be running on :8000.
#
#   1) build the Mini App once (backend serves it at /app):
#        cd apps/mini-app && npm install && npm run build
#   2) run the backend:  make run-backend
#   3) in another terminal:  bash scripts/free-tunnel.sh
#
# Then in @BotFather: /setmenubutton -> https://<printed-url>/app
set -euo pipefail

PORT="${1:-8000}"

if ! command -v cloudflared >/dev/null 2>&1; then
    echo "cloudflared не установлен. Установите (бесплатно, без регистрации):"
    echo "  • Linux:   https://pkg.cloudflare.com/  (пакет cloudflared)"
    echo "  • macOS:   brew install cloudflared"
    echo "  • Windows: winget install --id Cloudflare.cloudflared"
    echo "Альтернатива: npx localtunnel --port $PORT"
    exit 1
fi

echo "==> Открываю бесплатный HTTPS-туннель к http://127.0.0.1:$PORT ..."
echo "    Скопируйте выданный https://<...>.trycloudflare.com URL и укажите в"
echo "    @BotFather: /setmenubutton -> <url>/app"
echo
exec cloudflared tunnel --url "http://127.0.0.1:$PORT"
