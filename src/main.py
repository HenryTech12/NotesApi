# src/main.py
from fastapi import FastAPI, status
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from src.routers import notes
from src.middleware.logger import RequestLoggerMiddleware
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
app.add_middleware(RequestLoggerMiddleware)

# Exception Handlers
app.add_exception_handler(Exception, global_exception_handler)
app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)

# Routes
@app.get("/api/v1/health", status_code=status.HTTP_200_OK)
async def health_check():
    return {"status": "ok"}

app.include_router(notes.router, prefix="/api/v1")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=3000)
