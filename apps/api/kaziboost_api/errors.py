from fastapi import HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse


def _request_id(request: Request) -> str | None:
    return getattr(request.state, "request_id", None)


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    detail = exc.detail
    code = "http_error"
    if exc.status_code == 400:
        code = "bad_request"
    elif exc.status_code == 401:
        code = "unauthorized"
    elif exc.status_code == 403:
        code = "forbidden"
    elif exc.status_code == 404:
        code = "not_found"
    elif exc.status_code == 409:
        code = "conflict"
    elif exc.status_code == 429:
        code = "rate_limited"

    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": detail, "code": code, "request_id": _request_id(request)},
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors(), "code": "validation_error", "request_id": _request_id(request)},
    )
