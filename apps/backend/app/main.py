"""FastAPI application entry point.

Wires together: REST API, the agent WebSocket, the Telegram bot (polling in
LOCAL_MVP, webhook in FULL), the scheduler tick and the device watchdog.
"""

from __future__ import annotations

import asyncio
import contextlib
from collections.abc import AsyncIterator
from pathlib import Path

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import FastAPI, Request, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse

from .api.routers import api_router
from .core.config import AppMode, settings
from .core.errors import DomainError
from .core.logging import configure_logging, get_logger
from .core.security import decode_access_token
from .db.base import Base
from .db.seed import seed_all
from .db.session import SessionLocal, engine
from .services.background import device_watchdog, schedule_tick
from .websocket.agent import agent_ws_endpoint
from .websocket.hub import hub

log = get_logger("main")


async def _startup_db() -> None:
    # LOCAL_MVP: create tables directly for a one-command start. FULL uses Alembic.
    if settings.app_mode == AppMode.LOCAL_MVP:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    async with SessionLocal() as session:
        token = await seed_all(session)
        await session.commit()
        if token:
            log.warning(
                "generated_device_token",
                hint="set AGENT_DEVICE_TOKEN",
                token_preview=token[:6] + "…",
            )


def _build_scheduler() -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler(timezone="UTC")
    scheduler.add_job(schedule_tick, "interval", seconds=15, id="schedule_tick", max_instances=1)
    scheduler.add_job(
        device_watchdog, "interval", seconds=10, id="device_watchdog", max_instances=1
    )
    return scheduler


@contextlib.asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    configure_logging()
    log.info("starting", mode=settings.app_mode.value, tz=settings.app_timezone)
    await _startup_db()

    from .bot.setup import bot_runtime

    await bot_runtime.start()
    scheduler = _build_scheduler()
    scheduler.start()
    log.info("ready")
    try:
        yield
    finally:
        scheduler.shutdown(wait=False)
        await bot_runtime.stop()
        await engine.dispose()
        log.info("stopped")


def create_app() -> FastAPI:
    app = FastAPI(
        title="Живая вода • Рупор — Audio Control API",
        version="1.0.0",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ── Error handling: friendly JSON, never a traceback ─────────────────────
    @app.exception_handler(DomainError)
    async def _domain_error(_: Request, exc: DomainError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": exc.message, "code": exc.code},
        )

    app.include_router(api_router)

    @app.get("/health")
    async def health() -> dict:
        return {"status": "ok", "mode": settings.app_mode.value}

    # ── Agent WebSocket ──────────────────────────────────────────────────────
    @app.websocket("/ws/agent")
    async def ws_agent(websocket: WebSocket) -> None:
        await agent_ws_endpoint(websocket)

    # ── Admin live updates (SSE) ─────────────────────────────────────────────
    @app.get("/api/admin/events")
    async def admin_events(token: str = "") -> StreamingResponse:
        decode_access_token(token)  # raises AuthError -> handled -> 401

        async def _stream() -> AsyncIterator[str]:
            queue = hub.subscribe_admin()
            try:
                yield "event: hello\ndata: {}\n\n"
                while True:
                    try:
                        event = await asyncio.wait_for(queue.get(), timeout=25)
                        import json

                        yield f"data: {json.dumps(event)}\n\n"
                    except TimeoutError:
                        yield ": keep-alive\n\n"
            finally:
                hub.unsubscribe_admin(queue)

        return StreamingResponse(_stream(), media_type="text/event-stream")

    # ── Telegram webhook (FULL) ──────────────────────────────────────────────
    @app.post("/telegram/webhook")
    async def telegram_webhook(request: Request) -> JSONResponse:
        from aiogram.types import Update

        from .bot.setup import bot_runtime

        if settings.telegram_webhook_secret:
            header = request.headers.get("X-Telegram-Bot-Api-Secret-Token")
            if header != settings.telegram_webhook_secret:
                return JSONResponse(status_code=403, content={"error": "forbidden"})
        if bot_runtime.bot is None or bot_runtime.dp is None:
            return JSONResponse(status_code=503, content={"error": "bot not ready"})
        update = Update.model_validate(await request.json(), context={"bot": bot_runtime.bot})
        await bot_runtime.dp.feed_update(bot_runtime.bot, update)
        return JSONResponse(content={"ok": True})

    # ── Optional: serve built Mini App ───────────────────────────────────────
    dist = Path(__file__).resolve().parents[2] / "mini-app" / "dist"
    if settings.mini_app_enabled and dist.exists():
        from fastapi.staticfiles import StaticFiles

        app.mount("/app", StaticFiles(directory=str(dist), html=True), name="mini-app")

    return app


app = create_app()


def run() -> None:  # console entry point
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=False)
