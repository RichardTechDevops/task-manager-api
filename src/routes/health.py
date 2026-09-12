from fastapi import APIRouter

from src.rate_limit import limiter

router = APIRouter()


@router.get("/health")
@limiter.exempt
def health_check() -> dict:
    return {"status": "ok"}
