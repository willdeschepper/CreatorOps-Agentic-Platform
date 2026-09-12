from collections.abc import Mapping
from typing import Any

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse


class DomainError(Exception):
    def __init__(
        self,
        status_code: int,
        code: str,
        detail: str,
        *,
        meta: Mapping[str, Any] | None = None,
    ) -> None:
        super().__init__(detail)
        self.status_code = status_code
        self.code = code
        self.detail = detail
        self.meta = dict(meta or {})


class NotFoundError(DomainError):
    def __init__(self, code: str, detail: str) -> None:
        super().__init__(404, code, detail)


class ConflictError(DomainError):
    def __init__(self, code: str, detail: str, *, meta: Mapping[str, Any] | None = None) -> None:
        super().__init__(409, code, detail, meta=meta)


class ForbiddenError(DomainError):
    def __init__(self, code: str = "forbidden", detail: str = "Access denied") -> None:
        super().__init__(403, code, detail)


class UnauthorizedError(DomainError):
    def __init__(self, detail: str = "Invalid credentials") -> None:
        super().__init__(401, "unauthorized", detail)


class UnprocessableError(DomainError):
    def __init__(self, code: str, detail: str, *, meta: Mapping[str, Any] | None = None) -> None:
        super().__init__(422, code, detail, meta=meta)


def install_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(DomainError)
    async def handle_domain_error(request: Request, error: DomainError) -> JSONResponse:
        body: dict[str, Any] = {
            "type": f"https://creatorops.local/problems/{error.code}",
            "title": error.code.replace("_", " ").title(),
            "status": error.status_code,
            "detail": error.detail,
            "instance": str(request.url.path),
            "code": error.code,
        }
        if error.meta:
            body["meta"] = error.meta
        return JSONResponse(
            status_code=error.status_code,
            content=body,
            media_type="application/problem+json",
            headers={"WWW-Authenticate": "Bearer"} if error.status_code == 401 else None,
        )
