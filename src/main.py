# src/main.py
import yaml
from fastapi import FastAPI, status, Depends
from fastapi.openapi.utils import get_openapi
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from src.routers import notes
from src.routers.notes import verify_api_version
from src.middleware.logger import AzureTelemetryMiddleware
from src.middleware.error_handler import (
    global_exception_handler, 
    http_exception_handler, 
    validation_exception_handler
)
from src.utils.store import store

app = FastAPI(title="Notes API", version="1.0.0")

# Seed data
store.seed()

# Middleware
app.add_middleware(AzureTelemetryMiddleware)

# Exception Handlers
app.add_exception_handler(Exception, global_exception_handler)
app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)

# Custom OpenAPI
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    try:
        with open("openapi.yaml", "r") as f:
            openapi_schema = yaml.safe_load(f)
        app.openapi_schema = openapi_schema
        return app.openapi_schema
    except Exception:
        return get_openapi(
            title=app.title,
            version=app.version,
            routes=app.routes,
        )

app.openapi = custom_openapi

# Routes
@app.get("/health", status_code=status.HTTP_200_OK, dependencies=[Depends(verify_api_version)])
async def health_check():
    return {"status": "ok"}

app.include_router(notes.router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=3000)
