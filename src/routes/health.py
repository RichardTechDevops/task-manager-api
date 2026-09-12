"""Health check route used by Docker and Kubernetes probes."""

from fastapi import APIRouter

from src.rate_limit import limiter

router = APIRouter()


@router.get("/health")
@limiter.exempt
def health_check() -> dict:
    """Return a simple service status payload."""
    return {"status": "ok"}
