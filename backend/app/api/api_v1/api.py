from fastapi import APIRouter

from app.api.api_v1.endpoints import properties, users, auth, brokers, brokerages, subscriptions, admin

api_router = APIRouter()
api_router.include_router(properties.router, prefix="/properties", tags=["properties"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(brokers.router, prefix="/brokers", tags=["brokers"])
api_router.include_router(brokerages.router, prefix="/brokerages", tags=["brokerages"])
api_router.include_router(subscriptions.router, prefix="/subscriptions", tags=["subscriptions"])
api_router.include_router(admin.router, prefix="/admin", tags=["admin"]) 