"""FastAPI application entrypoint."""

import logging
import time

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException

from src.logging_config import setup_logging
from src.rate_limit import limiter
from src.routes.health import router as health_router
from src.routes.tasks import router as tasks_router

setup_logging()
logger = logging.getLogger("task_manager")

app = FastAPI(
    title="Task Manager API",
    version="1.0.0",
    description=(
        "A lightweight RESTful task management service with in-memory storage, "
        "OpenAPI docs, request logging, and rate limiting."
    ),
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Write an access log for every request, including failures."""
    started = time.perf_counter()
    try:
        response = await call_next(request)
    except Exception:
        duration_ms = (time.perf_counter() - started) * 1000
        logger.exception(
            "unhandled error method=%s path=%s duration_ms=%.2f",
            request.method,
            request.url.path,
            duration_ms,
        )
        raise

    duration_ms = (time.perf_counter() - started) * 1000
    logger.info(
        "request method=%s path=%s status=%s duration_ms=%.2f",
        request.method,
        request.url.path,
        response.status_code,
        duration_ms,
    )
    return response


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """Return a consistent JSON error body for HTTP exceptions."""
    logger.warning(
        "http error method=%s path=%s status=%s detail=%s",
        request.method,
        request.url.path,
        exc.status_code,
        exc.detail,
    )
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Return 400 for invalid request bodies instead of FastAPI's default 422."""
    logger.warning(
        "validation error method=%s path=%s errors=%s",
        request.method,
        request.url.path,
        exc.errors(),
    )
    safe_errors = []
    for item in exc.errors():
        safe_errors.append(
            {
                "type": item.get("type"),
                "loc": item.get("loc"),
                "msg": item.get("msg"),
            }
        )
    return JSONResponse(
        status_code=400,
        content={"detail": "Invalid request body", "errors": safe_errors},
    )


app.include_router(health_router)
app.include_router(tasks_router)
