from fastapi import APIRouter

from .endpoints import properties, users, auth, brokers, brokerages, subscriptions, admin #, corrections
from backend.scripts.batch_geocode_api import router as batch_geocode_router

api_router = APIRouter()
api_router.include_router(properties.router, prefix="/properties", tags=["properties"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(brokers.router, prefix="/brokers", tags=["brokers"])
api_router.include_router(brokerages.router, prefix="/brokerages", tags=["brokerages"])
api_router.include_router(subscriptions.router, prefix="/subscriptions", tags=["subscriptions"])
api_router.include_router(admin.router, prefix="/admin", tags=["admin"])
# Comment out corrections router inclusion
# api_router.include_router(corrections.router, prefix="/corrections", tags=["corrections"])
api_router.include_router(batch_geocode_router, prefix="/admin/geocoding", tags=["geocoding"]) 