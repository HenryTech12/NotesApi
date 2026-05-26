# src/main.py
import yaml
import os
from fastapi import FastAPI, status, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from src.routers import notes, auth, admin
from src.routers.notes import verify_api_version
from src.middleware.logger import AzureTelemetryMiddleware
from src.middleware.error_handler import (
    global_exception_handler, 
    http_exception_handler, 
    validation_exception_handler
)

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Verify JWT Secret
JWT_SECRET = os.getenv("JWT_SECRET")
if not JWT_SECRET or len(JWT_SECRET) < 32:
    raise ValueError("JWT_SECRET environment variable is missing or less than 32 characters.")

app = FastAPI(title="Notes API", version="1.0.0")

# Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
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

app.include_router(auth.router)
app.include_router(notes.router)
app.include_router(admin.router)

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 3000))
    uvicorn.run(app, host="0.0.0.0", port=port)
