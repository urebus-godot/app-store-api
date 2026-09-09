import traceback
import logging

from fastapi import status, APIRouter
from fastapi.responses import JSONResponse

from sqlalchemy import text

from app.api.deps import RedisDep, SessionDep


router = APIRouter(tags=["Server"])

logger = logging.getLogger("api.v1.server")


@router.get("/health")
async def health_check(
    redis: RedisDep,
    session: SessionDep
) -> dict[str, str]:
    """Performs a health check by attempting to connect 
    to Redis and Postgres database.
    
    *Returns*: dict object containing status and error detail if it occurred."""
    try:
        redis_response = await redis.ping()
        db_response = await session.exec(text("SELECT 1"))

        if not redis_response:
            return JSONResponse(
            content={"status": "Unhealthy", "detail": "Connection to Redis failed"},
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE
        )
        
        return {"status": "Healthy"}
    except Exception as e:
        error_string = traceback.format_exc()
        logger.error(error_string)
        return JSONResponse(
            content={"status": "Unhealthy", "detail": str(e)},
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE
        )