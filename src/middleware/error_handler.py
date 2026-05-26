# src/middleware/error_handler.py
import logging
from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger("fastapi")

async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Global exception caught: {str(exc)}", exc_info=True)
    code = "InternalServerError"
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        headers={"x-ms-error-code": code},
        content={
            "error": {
                "code": code,
                "message": "An unexpected error occurred on the server."
            }
        },
    )

async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    code_map = {404: "ResourceNotFound", 409: "Conflict", 403: "Forbidden", 401: "Unauthorized"}
    
    # If detail is already a structured dict, use it directly as the error body
    if isinstance(exc.detail, dict):
        return JSONResponse(
            status_code=exc.status_code,
            headers={"x-ms-error-code": exc.detail.get("code", "ServiceError")},
            content={"error": exc.detail}
        )
    
    code = code_map.get(exc.status_code, "ServiceError")
    return JSONResponse(
        status_code=exc.status_code,
        headers={"x-ms-error-code": code},
        content={"error": {"code": code, "message": str(exc.detail)}}
    )

async def validation_exception_handler(request: Request, exc: RequestValidationError):
    code = "InvalidRequest"
    details = []
    for error in exc.errors():
        field = str(error['loc'][-1])
        details.append({
            "code": "InvalidField",
            "target": field,
            "message": error['msg']
        })

    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST, # Azure prefers 400 for validation errors over 422
        headers={"x-ms-error-code": code},
        content={
            "error": {
                "code": code,
                "message": "The request is invalid.",
                "details": details
            }
        },
    )
