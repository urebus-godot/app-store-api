import logging

from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import ResponseValidationError

import botocore.exceptions as boto_exceptions

import httpx

logger = logging.getLogger("app.exception_handlers")


def response_validation_error_handler(
    request: Request, exception: ResponseValidationError
) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        content={"errors": exception.errors()},
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


def boto_client_error_handler(
    request: Request, exception: boto_exceptions.ClientError
) -> JSONResponse:
    logger.error(f"Boto client error: {exception.errors()}")
    return JSONResponse(
        status_code=status.HTTP_502_BAD_GATEWAY,
        content={"message": "Boto client error occurred", "errors": exception.errors()},
    )
