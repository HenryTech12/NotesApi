# src/middleware/logger.py
import time
import uuid
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from datetime import datetime

class AzureTelemetryMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        
        # Capture client correlation ID if provided
        client_id = request.headers.get("x-ms-client-request-id")
        
        response = await call_next(request)
        process_time = int((time.time() - start_time) * 1000)
        
        # Inject mandatory tracking headers
        response.headers["x-ms-request-id"] = str(uuid.uuid4())
        if client_id:
            response.headers["x-ms-client-request-id"] = client_id
        
        status_code = response.status_code
        method = request.method
        url = request.url.path
        timestamp = datetime.now().isoformat()

        # ANSI colors
        green = "\033[32m"
        yellow = "\033[33m"
        red = "\033[31m"
        reset = "\033[0m"

        color = green
        if 400 <= status_code < 500:
            color = yellow
        elif status_code >= 500:
            color = red

        print(f"{timestamp} | {color}{status_code}{reset} | {method} | {url} | {process_time}ms")
        
        return response
