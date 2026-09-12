# 健康检查路由。
# Docker healthcheck、K8s livenessProbe / readinessProbe 都访问这个接口。
from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
def health_check() -> dict:
    # 作业要求返回服务状态，状态码 200。
    return {"status": "ok"}
