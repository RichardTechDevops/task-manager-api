# FastAPI 应用入口。
# uvicorn 启动命令：uvicorn src.app:app --host 0.0.0.0 --port 8080
import logging
import time

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from src.logging_config import setup_logging
from src.routes.health import router as health_router
from src.routes.tasks import router as tasks_router

# 进程启动时先配日志，后面中间件和异常处理才能打出请求/错误日志。
setup_logging()
logger = logging.getLogger("task_manager")

app = FastAPI(
    title="Task Manager API",
    version="1.0.0",
    description="Task Manager REST API",
    docs_url="/docs",          # Swagger UI
    redoc_url="/redoc",        # ReDoc
    openapi_url="/openapi.json",
)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    # 请求日志：方法、路径、状态码、耗时。
    # 未捕获异常走 exception 日志，满足作业“请求日志 + 错误日志”。
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
    # 把 404 等 HTTP 异常统一成 JSON：{"detail": "..."}。
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
    # FastAPI 默认校验失败是 422，作业要求 POST 非法输入返回 400，这里改掉。
    # ctx 里可能有 ValueError，不能直接 json.dumps，所以只挑 type/loc/msg。
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
