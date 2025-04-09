"""
Main FastAPI application module.
"""

import asyncio
import logging
import os
import sys
import time
from typing import List

import sentry_sdk
import socketio
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from sentry_sdk.integrations.fastapi import FastApiIntegration
from starlette.middleware.sessions import SessionMiddleware

# Relative imports for app components
from .core.config import settings
from .api.api_v1.api import api_router
from .core.dependencies import get_current_user
from .schemas import User
from .utils.error_handling import add_error_handlers
from .utils.auth_session import AuthSessionMiddleware
from .utils.monitoring import record_api_call, start_metrics_monitoring
from .middleware.exception_handler import ExceptionHandlerMiddleware
from .middleware.request_tracker import RequestTrackerMiddleware
from .middleware.rate_limiter import RateLimiterMiddleware
from .db.session import engine, SessionLocal

# Import the batch_geocode_api router from scripts
# Keep this sys.path logic for now, although it's not ideal
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# TODO: Consider a better way to integrate script-based routers if needed
# Maybe move the geocoding API into the main app structure?
from scripts.batch_geocode_api import router as geocoding_router

# Initialize Sentry if DSN is provided
# if settings.SENTRY_DSN:
#     sentry_sdk.init(
#         dsn=settings.SENTRY_DSN,
#         environment=settings.SENTRY_ENVIRONMENT,
#         traces_sample_rate=settings.SENTRY_TRACES_SAMPLE_RATE,
#         integrations=[FastApiIntegration()]
#     )

# Setup CORS for Socket.IO
sio_origins_list: List[str] = []
if settings.SOCKETIO_CORS_ORIGINS:
    sio_origins_list = [origin.strip() for origin in settings.SOCKETIO_CORS_ORIGINS.split(',')]
sio = socketio.AsyncServer(
    async_mode='asgi', 
    cors_allowed_origins=sio_origins_list
)

# Setup CORS for FastAPI
app_origins_list: List[str] = []
if settings.CORS_ORIGINS:
    app_origins_list = [origin.strip() for origin in settings.CORS_ORIGINS.split(',')]

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=app_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add session middleware
app.add_middleware(
    SessionMiddleware, 
    secret_key=settings.AUTH_SECRET_KEY,
    max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60
)

# Add custom AuthSessionMiddleware
app.add_middleware(AuthSessionMiddleware)

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

# Mount Socket.IO app
socket_app = socketio.ASGIApp(sio, other_asgi_app=app)

# Include API router
app.include_router(api_router, prefix=settings.API_V1_STR)

# Include geocoding router
app.include_router(
    geocoding_router, 
    prefix=f"{settings.API_V1_STR}/admin/geocoding",
    tags=["geocoding"]
)

# Add error handlers
add_error_handlers(app)

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

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# For direct uvicorn execution
if __name__ == "__main__":
    import uvicorn
    # Adjust the run command to use the relative path if needed when run directly
    # This depends on how you execute this script.
    # If run from the `backend` directory: uvicorn app.main:socket_app ...
    # If run from the workspace root: uvicorn backend.app.main:socket_app ...
    uvicorn.run("app.main:socket_app", host="0.0.0.0", port=8000, reload=True) 