# src/middleware/error_handler.py
from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

async def global_exception_handler(request: Request, exc: Exception):
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
    # Map status codes to machine-readable codes where possible
    code = "ServiceError"
    if exc.status_code == 404:
        code = "ResourceNotFound"
    elif exc.status_code == 409:
        code = "Conflict"
    elif exc.status_code == 403:
        code = "Forbidden"
    elif exc.status_code == 401:
        code = "Unauthorized"
    
    return JSONResponse(
        status_code=exc.status_code,
        headers={"x-ms-error-code": code},
        content={
            "error": {
                "code": code,
                "message": str(exc.detail)
            }
        },
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
