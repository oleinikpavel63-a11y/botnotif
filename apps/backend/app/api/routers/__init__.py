from __future__ import annotations

from fastapi import APIRouter

from . import agent, audit, auth, devices, me, scenarios, schedules, system, tracks, users

api_router = APIRouter(prefix="/api")
api_router.include_router(auth.router)
api_router.include_router(me.router)
api_router.include_router(devices.router)
api_router.include_router(tracks.router)
api_router.include_router(scenarios.router)
api_router.include_router(schedules.router)
api_router.include_router(users.router)
api_router.include_router(audit.router)
api_router.include_router(system.router)
api_router.include_router(agent.router)

__all__ = ["api_router"]
