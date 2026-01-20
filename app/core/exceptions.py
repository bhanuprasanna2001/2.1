"""Custom exceptions and exception handlers.

This module defines the application's exception hierarchy and registers
global exception handlers for FastAPI.
"""

from enum import StrEnum
from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel


class ErrorCode(StrEnum):
    """Machine-readable error codes for API consumers."""

    # Resource errors
    BOOKMARK_NOT_FOUND = "BOOKMARK_NOT_FOUND"
    COLLECTION_NOT_FOUND = "COLLECTION_NOT_FOUND"
    TAG_NOT_FOUND = "TAG_NOT_FOUND"
    USER_NOT_FOUND = "USER_NOT_FOUND"
    RESOURCE_NOT_FOUND = "RESOURCE_NOT_FOUND"

    # Validation errors
    VALIDATION_ERROR = "VALIDATION_ERROR"
    DUPLICATE_RESOURCE = "DUPLICATE_RESOURCE"
    INVALID_URL = "INVALID_URL"

    # Authentication errors
    INVALID_CREDENTIALS = "INVALID_CREDENTIALS"
    TOKEN_EXPIRED = "TOKEN_EXPIRED"
    TOKEN_INVALID = "TOKEN_INVALID"
    UNAUTHORIZED = "UNAUTHORIZED"
    FORBIDDEN = "FORBIDDEN"

    # Server errors
    INTERNAL_ERROR = "INTERNAL_ERROR"
    DATABASE_ERROR = "DATABASE_ERROR"


class ErrorDetail(BaseModel):
    """Detail for a single validation error."""

    field: str
    message: str


class ErrorResponse(BaseModel):
    """Structured error response format."""

    code: str
    message: str
    details: list[ErrorDetail] | None = None
    request_id: str | None = None


class ErrorWrapper(BaseModel):
    """Wrapper for error response."""

    error: ErrorResponse


class AppException(Exception):
    """Base exception for all application errors.

    Attributes:
        code: Machine-readable error code.
        message: Human-readable error message.
        status_code: HTTP status code.
        details: Additional error details.
    """

    status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR
    code: ErrorCode = ErrorCode.INTERNAL_ERROR

    def __init__(
        self,
        message: str = "An unexpected error occurred",
        *,
        code: ErrorCode | None = None,
        details: list[dict[str, str]] | None = None,
    ) -> None:
        self.message = message
        if code is not None:
            self.code = code
        self.details = details
        super().__init__(message)

    def to_response(self, request_id: str | None = None) -> dict[str, Any]:
        """Convert exception to error response format."""
        error_details = None
        if self.details:
            error_details = [ErrorDetail(**d) for d in self.details]

        return ErrorWrapper(
            error=ErrorResponse(
                code=self.code,
                message=self.message,
                details=error_details,
                request_id=request_id,
            )
        ).model_dump()


class NotFoundError(AppException):
    """Resource not found error."""

    status_code = status.HTTP_404_NOT_FOUND
    code = ErrorCode.RESOURCE_NOT_FOUND

    def __init__(
        self,
        resource: str = "Resource",
        resource_id: Any = None,
        *,
        code: ErrorCode | None = None,
    ) -> None:
        message = f"{resource} not found"
        if resource_id is not None:
            message = f"{resource} with id '{resource_id}' not found"
        super().__init__(message, code=code)


class ValidationError(AppException):
    """Validation error for invalid input."""

    status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
    code = ErrorCode.VALIDATION_ERROR


class ConflictError(AppException):
    """Conflict error for duplicate resources."""

    status_code = status.HTTP_409_CONFLICT
    code = ErrorCode.DUPLICATE_RESOURCE

    def __init__(
        self,
        resource: str = "Resource",
        field: str | None = None,
        value: Any = None,
    ) -> None:
        if field and value:
            message = f"{resource} with {field} '{value}' already exists"
        else:
            message = f"{resource} already exists"
        super().__init__(message)


class AuthenticationError(AppException):
    """Authentication error for invalid credentials or tokens."""

    status_code = status.HTTP_401_UNAUTHORIZED
    code = ErrorCode.INVALID_CREDENTIALS


class AuthorizationError(AppException):
    """Authorization error for forbidden access."""

    status_code = status.HTTP_403_FORBIDDEN
    code = ErrorCode.FORBIDDEN


def get_request_id(request: Request) -> str | None:
    """Extract request ID from request state."""
    return getattr(request.state, "request_id", None)


async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    """Handle application-specific exceptions."""
    return JSONResponse(
        status_code=exc.status_code,
        content=exc.to_response(get_request_id(request)),
    )


async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Handle Pydantic validation errors."""
    details = []
    for error in exc.errors():
        # Extract field name from location tuple
        loc = error.get("loc", ())
        field = ".".join(str(x) for x in loc[1:]) if len(loc) > 1 else str(loc[0])
        details.append({"field": field, "message": error.get("msg", "Invalid value")})

    validation_error = ValidationError(
        message="Request validation failed",
        details=details,
    )

    return JSONResponse(
        status_code=validation_error.status_code,
        content=validation_error.to_response(get_request_id(request)),
    )


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle unexpected exceptions."""
    # Log the actual error
    print(f"Unexpected error: {exc!r}")

    error = AppException(
        message="An unexpected error occurred",
        code=ErrorCode.INTERNAL_ERROR,
    )

    return JSONResponse(
        status_code=error.status_code,
        content=error.to_response(get_request_id(request)),
    )


def register_exception_handlers(app: FastAPI) -> None:
    """Register all exception handlers with the FastAPI app."""
    app.add_exception_handler(AppException, app_exception_handler)  # type: ignore[arg-type]
    app.add_exception_handler(RequestValidationError, validation_exception_handler)  # type: ignore[arg-type]
    app.add_exception_handler(Exception, generic_exception_handler)
