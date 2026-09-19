import time

from fastapi import status, APIRouter
from fastapi.responses import JSONResponse

from sqlalchemy import text

from app.task_queue.celery_app import celery_app

from app.api.deps import RedisDep, SessionDep


router = APIRouter(tags=["Server"])


@router.get("/live")
async def liveness_probe() -> dict:
    """Liveness probe: checks whether the FastAPI app is running
    
    *Returns*: dict object containing status and timestamp"""
    return {"status": "ok", "timestamp": time.time()}


@router.get("/ready")
async def readiness_probe(
    redis: RedisDep,
    session: SessionDep
) -> dict[str, str]:
    """Readiness probe: Checks the availability of services 
    on which the app depends.
    
    *Returns*: JSONResponse object containing status of dependencies"""
    status_code = status.HTTP_200_OK
    service_statuses = {
        "db": "unknown",
        "redis": "unknown",
        "celery": "unknown"
    }

    try:
        await session.exec(text("SELECT 1"))
        service_statuses["db"] = "ok"
    except Exception as e:
        service_statuses["db"] = f"error: {e}"
        status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    try:
        await redis.ping()
        service_statuses["redis"] = "ok"
    except Exception as e:
        service_statuses["redis"] = f"error: {e}"
        status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    try:
        inspect = celery_app.control.inspect(timeout=1.0)
        active_workers = inspect.active()

        if active_workers:
            service_statuses["celery"] = "ok"
        else:
            service_statuses["celery"] = "error: No active workers found"
            status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    except Exception as e:
        service_statuses["celery"] = f"error: {e}"
        status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    return JSONResponse(
        content={
            "status": "ok" if status_code == status.HTTP_200_OK else "error",
            "services": service_statuses,
            "timestamp": time.time()
        },
        status_code=status_code
    )