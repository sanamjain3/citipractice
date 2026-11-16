import logging

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

from app.database import Database
from app.dependencies import get_database
from app.schemas import HealthResponse

router = APIRouter(tags=["health"])
logger = logging.getLogger("app.health")


@router.get("/health", response_model=HealthResponse, responses={503: {"model": HealthResponse}})
def health(db: Database = Depends(get_database)):
    try:
        db.ping()
    except Exception:
        logger.exception("database health check failed")
        return JSONResponse(status_code=503, content={"status": "degraded", "database": "unreachable"})
    return HealthResponse(status="ok", database="ok")
