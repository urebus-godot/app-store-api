from fastapi import Request, status
from fastapi.responses import JSONResponse

from app.main import app


@app.exception_handler(ValueError)
async def value_error_handler(
    request: Request, exception: ValueError
) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        content={"message": exception},
    )


@app.exception_handler(FileNotFoundError)
async def file_not_found_error_handler(
    request: Request, exception: FileNotFoundError
) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"message": "File not found"},
    )
