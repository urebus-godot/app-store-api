from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import ResponseValidationError

import httpx

from app.core.logging import logger


#def value_error_handler(
#    request: Request, exception: ValueError
#) -> JSONResponse:
#    return JSONResponse(
#        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
#        content={"message": exception},
#    )


def file_not_found_error_handler(
    request: Request, exception: FileNotFoundError
) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"message": "File not found"},
    )


def response_validation_error_handler(
    request: Request, exception: ResponseValidationError
) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        content={"message": exception.errors()},
    )


def request_error_handler(
    request: Request, exception: httpx.RequestError
) -> JSONResponse:
    logger.error(f"Request exception: {exception.errors()}")
    return JSONResponse(
        status_code=status.HTTP_502_BAD_GATEWAY,
        content={"message": "Error while sending request to API"},
    )


def timeout_error_handler(
    request: Request, exception: httpx.ReadTimeout
) -> JSONResponse:
    logger.error(f"Timeout exception: {exception.errors()}")
    return JSONResponse(
        status_code=status.HTTP_504_GATEWAY_TIMEOUT,
        content={"message": "Response timeout expired"},
    )