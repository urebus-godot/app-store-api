import logging

from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import ResponseValidationError

import botocore.exceptions as boto_exceptions
import httpx

from app.core.exceptions import InvalidFileTypeError

logger = logging.getLogger("core.exception_handlers")


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
    logger.error(f"Request exception: {exception}")
    return JSONResponse(
        status_code=status.HTTP_502_BAD_GATEWAY,
        content={"message": "Error while sending request to API"},
    )


def timeout_error_handler(
    request: Request, exception: httpx.ReadTimeout
) -> JSONResponse:
    logger.error(f"Timeout exception: {exception}")
    return JSONResponse(
        status_code=status.HTTP_504_GATEWAY_TIMEOUT,
        content={"message": "Response timeout"},
    )


def boto_client_error_handler(
    request: Request, exception: boto_exceptions.ClientError
) -> JSONResponse:
    logger.error(f"Boto client error: {exception.errors()}")
    return JSONResponse(
        status_code=status.HTTP_502_BAD_GATEWAY,
        content={
            "message": "Boto client error occurred", 
            "errors": exception.errors()
        },
    )


def invalid_file_type_error_handler(
    request: Request, exception: InvalidFileTypeError
) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
        content={
            "detail": "Invalid type of file"
        },
    )


exception_handlers = {
    ResponseValidationError: response_validation_error_handler,
    httpx.RequestError: request_error_handler,
    httpx.ReadTimeout: timeout_error_handler,
    boto_exceptions.ClientError: boto_client_error_handler,
    InvalidFileTypeError: invalid_file_type_error_handler
}