from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.schemas.brokerage import Brokerage, BrokerageCreate, BrokerageUpdate
from app.services.brokerage_service import BrokerageService

router = APIRouter()

@router.get("/", response_model=List[Brokerage])
async def get_brokerages(
    skip: int = 0,
    limit: int = 100,
    name: Optional[str] = Query(None, description="Filter by brokerage name"),
    brokerage_service: BrokerageService = Depends()
):
    """
    Get all brokerages with optional filtering.
    """
    return await brokerage_service.get_brokerages(
        skip=skip,
        limit=limit,
        name=name
    )

@router.get("/{brokerage_id}", response_model=Brokerage)
async def get_brokerage(
    brokerage_id: str,
    brokerage_service: BrokerageService = Depends()
):
    """
    Get a specific brokerage by ID.
    """
    brokerage_data = await brokerage_service.get_brokerage(brokerage_id)
    if brokerage_data is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Brokerage not found"
        )
    return brokerage_data

@router.post("/", response_model=Brokerage, status_code=status.HTTP_201_CREATED)
async def create_brokerage(
    brokerage_data: BrokerageCreate,
    brokerage_service: BrokerageService = Depends()
):
    """
    Create a new brokerage.
    """
    return await brokerage_service.create_brokerage(brokerage_data)

@router.put("/{brokerage_id}", response_model=Brokerage)
async def update_brokerage(
    brokerage_id: str,
    brokerage_data: BrokerageUpdate,
    brokerage_service: BrokerageService = Depends()
):
    """
    Update a brokerage.
    """
    updated_brokerage = await brokerage_service.update_brokerage(brokerage_id, brokerage_data)
    if updated_brokerage is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Brokerage not found"
        )
    return updated_brokerage

@router.delete("/{brokerage_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_brokerage(
    brokerage_id: str,
    brokerage_service: BrokerageService = Depends()
):
    """
    Delete a brokerage.
    """
    deleted = await brokerage_service.delete_brokerage(brokerage_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Brokerage not found"
        )
    return None 