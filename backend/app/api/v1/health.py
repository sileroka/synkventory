"""
Health check endpoints for monitoring and container orchestration.
"""

from datetime import datetime, timezone
from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import get_db
from app.schemas.responses import DataResponse

router = APIRouter()


@router.get("/health", response_model=DataResponse[dict])
def health_check(db: Session = Depends(get_db)):
    """
    Health check endpoint for load balancers and container orchestration.

    Returns the current status of the API and its dependencies.
    """
    # Check database connectivity
    db_status = "healthy"
    db_latency_ms = None
    try:
        start = datetime.now(timezone.utc)
        db.execute(text("SELECT 1"))
        end = datetime.now(timezone.utc)
        db_latency_ms = (end - start).total_seconds() * 1000
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"

    health_data = {
        "status": "healthy" if db_status == "healthy" else "degraded",
        "version": settings.VERSION,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "checks": {
            "database": {
                "status": db_status,
                "latencyMs": round(db_latency_ms, 2) if db_latency_ms else None,
            }
        },
    }

    return DataResponse(data=health_data)


@router.get("/health/live")
def liveness_check():
    """
    Kubernetes liveness probe endpoint.

    Returns 200 if the application is running.
    This should be a lightweight check that doesn't test dependencies.
    """
    return {"status": "alive"}


@router.get("/health/ready")
def readiness_check(db: Session = Depends(get_db)):
    """
    Kubernetes readiness probe endpoint.

    Returns 200 if the application is ready to accept traffic.
    This checks that all dependencies are available.
    """
    try:
        db.execute(text("SELECT 1"))
        return {"status": "ready"}
    except Exception:
        return {"status": "not ready"}, 503
