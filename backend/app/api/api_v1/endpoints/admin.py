from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from fastapi.security import OAuth2PasswordBearer

from app.services.user_service import UserService
from app.services.property_service import PropertyService
from app.services.broker_service import BrokerService
from app.services.brokerage_service import BrokerageService
from app.services.neo4j_sync import Neo4jSyncService

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

@router.get("/stats")
async def get_stats(
    token: str = Depends(oauth2_scheme),
    user_service: UserService = Depends(),
    property_service: PropertyService = Depends(),
    broker_service: BrokerService = Depends(),
    brokerage_service: BrokerageService = Depends()
):
    """
    Get admin statistics.
    """
    # Check if the user is an admin
    current_user = await user_service.get_current_user(token)
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    # Get counts
    property_count = await property_service.get_property_count()
    broker_count = await broker_service.get_broker_count()
    brokerage_count = await brokerage_service.get_brokerage_count()
    user_count = await user_service.get_user_count()
    
    return {
        "properties": property_count,
        "brokers": broker_count,
        "brokerages": brokerage_count,
        "users": user_count
    }

@router.post("/sync/neo4j")
async def sync_neo4j(
    background_tasks: BackgroundTasks,
    token: str = Depends(oauth2_scheme),
    user_service: UserService = Depends(),
    neo4j_sync_service: Neo4jSyncService = Depends()
):
    """
    Trigger a sync of all data to Neo4j.
    """
    # Check if the user is an admin
    current_user = await user_service.get_current_user(token)
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    # Start the sync in the background
    background_tasks.add_task(neo4j_sync_service.sync_all)
    
    return {"message": "Neo4j sync started"}

@router.post("/scrape")
async def trigger_scrape(
    background_tasks: BackgroundTasks,
    token: str = Depends(oauth2_scheme),
    user_service: UserService = Depends()
):
    """
    Trigger a scrape of property listings.
    """
    # Check if the user is an admin
    current_user = await user_service.get_current_user(token)
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    # This would normally trigger a Celery task to start the scraper
    # For now, we'll just return a message
    
    return {"message": "Scrape job started"} 