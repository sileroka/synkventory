from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError
from datetime import datetime
import uuid


def create_error_response(
    code: str, message: str, details: dict | None = None, request_id: str | None = None
) -> dict:
    """Create a standardized error response."""
    return {
        "error": {"code": code, "message": message, "details": details or {}},
        "meta": {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "request_id": request_id or str(uuid.uuid4()),
        },
    }


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Handle HTTP exceptions with standard error format."""
    # Map status codes to error codes
    error_codes = {
        400: "BAD_REQUEST",
        401: "UNAUTHORIZED",
        403: "FORBIDDEN",
        404: "NOT_FOUND",
        409: "CONFLICT",
        422: "VALIDATION_ERROR",
        500: "INTERNAL_SERVER_ERROR",
    }

    code = error_codes.get(exc.status_code, f"HTTP_{exc.status_code}")
    request_id = getattr(request.state, "request_id", str(uuid.uuid4()))

    return JSONResponse(
        status_code=exc.status_code,
        content=create_error_response(
            code=code, message=str(exc.detail), request_id=request_id
        ),
    )


async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Handle validation errors with standard error format."""
    request_id = getattr(request.state, "request_id", str(uuid.uuid4()))

    # Format validation errors
    errors = {}
    for error in exc.errors():
        field = ".".join(str(loc) for loc in error["loc"])
        errors[field] = error["msg"]

    return JSONResponse(
        status_code=422,
        content=create_error_response(
            code="VALIDATION_ERROR",
            message="Request validation failed",
            details={"validation_errors": errors},
            request_id=request_id,
        ),
    )


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle unexpected exceptions with standard error format."""
    request_id = getattr(request.state, "request_id", str(uuid.uuid4()))

    return JSONResponse(
        status_code=500,
        content=create_error_response(
            code="INTERNAL_SERVER_ERROR",
            message="An unexpected error occurred",
            request_id=request_id,
        ),
    )
