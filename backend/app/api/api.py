"""
API router for the application.
"""

from fastapi import APIRouter
from app.api.endpoints import brokers

api_router = APIRouter()

# Include broker routes
api_router.include_router(
    brokers.router, 
    prefix="/brokers", 
    tags=["brokers"], 
    responses={404: {"description": "Broker not found"}}
) 