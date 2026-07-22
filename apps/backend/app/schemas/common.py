from __future__ import annotations

from pydantic import BaseModel


class OkResponse(BaseModel):
    ok: bool = True
    message: str | None = None


class ErrorResponse(BaseModel):
    error: str
    code: str
    detail: str | None = None
