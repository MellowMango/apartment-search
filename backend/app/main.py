"""
Main FastAPI application module.
"""

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
import socketio
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
import time
import asyncio

from app.core.config import settings
from app.api.api import api_router
from backend.app.utils.monitoring import record_api_call, start_metrics_monitoring
from backend.app.middleware.exception_handler import ExceptionHandlerMiddleware
from backend.app.middleware.request_tracker import RequestTrackerMiddleware
from backend.app.middleware.rate_limiter import RateLimiterMiddleware

# Import the batch_geocode_api router
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scripts.batch_geocode_api import router as geocoding_router

# Initialize Sentry if DSN is provided
if settings.SENTRY_DSN:
    sentry_sdk.init(
        dsn=settings.SENTRY_DSN,
        environment=settings.SENTRY_ENVIRONMENT,
        traces_sample_rate=settings.SENTRY_TRACES_SAMPLE_RATE,
        integrations=[FastApiIntegration()]
    )

# Create Socket.IO server
sio = socketio.AsyncServer(
    async_mode='asgi',
    cors_allowed_origins=settings.CORS_ORIGINS
)

# Create FastAPI app
app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# Set up CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[str(origin) for origin in settings.CORS_ORIGINS],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add middleware components in the correct order
# Exception handling should be the first (outermost) middleware to catch all exceptions
app.add_middleware(ExceptionHandlerMiddleware)

# Request tracking middleware for logs and metrics
app.add_middleware(RequestTrackerMiddleware)

# Rate limiting middleware
app.add_middleware(
    RateLimiterMiddleware,
    rate_limits={
        # Default limits
        "*": settings.DEFAULT_RATE_LIMIT,
        "GET:*": settings.READ_RATE_LIMIT,
        "POST:*": settings.WRITE_RATE_LIMIT,
        "PUT:*": settings.WRITE_RATE_LIMIT,
        "DELETE:*": settings.WRITE_RATE_LIMIT,
        
        # Specific endpoint limits
        "GET:/api/v1/properties": settings.PROPERTIES_RATE_LIMIT,
        "*:/api/v1/admin/*": settings.ADMIN_RATE_LIMIT
    },
    exclude_paths=[
        "/health",
        f"{settings.API_V1_STR}/docs",
        f"{settings.API_V1_STR}/openapi.json",
        f"{settings.API_V1_STR}/redoc"
    ]
)

# Include API router
app.include_router(api_router, prefix=settings.API_V1_STR)

# Include geocoding router
app.include_router(
    geocoding_router, 
    prefix=f"{settings.API_V1_STR}/admin/geocoding",
    tags=["geocoding"]
)

# Create Socket.IO app
socket_app = socketio.ASGIApp(sio, app)

# Socket.IO events
@sio.event
async def connect(sid, environ):
    print(f"Client connected: {sid}")

@sio.event
async def disconnect(sid):
    print(f"Client disconnected: {sid}")

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}

# Start metrics monitoring on startup
@app.on_event("startup")
async def startup_event():
    # Start metrics monitoring in the background
    asyncio.create_task(
        start_metrics_monitoring(
            interval_seconds=3600,  # Save metrics hourly
            filepath_template="architecture_metrics_{timestamp}.json"
        )
    )
    print("Started architecture metrics monitoring")

# For direct uvicorn execution
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:socket_app", host="0.0.0.0", port=8000, reload=True) 