from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status

# Change to relative imports
from .... import schemas
from ....services.brokerage_service import BrokerageService
from ....core.dependencies import get_current_active_user
from ....schemas.api import APIResponse

router = APIRouter()

# Dependency injection for BrokerageService (example)
# def get_brokerage_service():
#     return BrokerageService()

@router.get("/", response_model=APIResponse[List[schemas.Brokerage]])
async def get_brokerages(
    skip: int = 0,
    limit: int = 100,
    name: Optional[str] = Query(None, description="Filter by brokerage name"),
    brokerage_service: BrokerageService = Depends()
):
    """
    Get all brokerages with optional filtering.
    """
    brokerages = await brokerage_service.get_brokerages(
        skip=skip,
        limit=limit,
        name=name
    )
    # Assuming get_brokerages returns a list that can be wrapped
    # Need total count for proper pagination if BrokerageService provides it
    total_count = len(brokerages) # Placeholder
    return APIResponse.paginated_response(
        data=brokerages, 
        page=(skip // limit) + 1, 
        page_size=limit, 
        total_items=total_count # Replace with actual total count if available
    )

@router.get("/{brokerage_id}", response_model=APIResponse[schemas.Brokerage])
async def get_brokerage(
    brokerage_id: str,
    brokerage_service: BrokerageService = Depends()
):
    """
    Get a specific brokerage by ID.
    """
    brokerage_data = await brokerage_service.get_brokerage(brokerage_id)
    if brokerage_data is None:
        raise NotFoundException(f"Brokerage with ID {brokerage_id} not found")
    return APIResponse.success_response(data=brokerage_data)

@router.post("/", response_model=APIResponse[schemas.Brokerage], status_code=status.HTTP_201_CREATED)
async def create_brokerage(
    brokerage_data: schemas.BrokerageCreate,
    brokerage_service: BrokerageService = Depends(),
    current_user: schemas.User = Depends(get_current_active_user) # Require auth to create
):
    """
    Create a new brokerage.
    """
    created_brokerage = await brokerage_service.create_brokerage(brokerage_data)
    return APIResponse.success_response(data=created_brokerage, message="Brokerage created successfully")

@router.put("/{brokerage_id}", response_model=APIResponse[schemas.Brokerage])
async def update_brokerage(
    brokerage_id: str,
    brokerage_data: schemas.BrokerageUpdate,
    brokerage_service: BrokerageService = Depends(),
    current_user: schemas.User = Depends(get_current_active_user) # Require auth to update
):
    """
    Update a brokerage.
    """
    updated_brokerage = await brokerage_service.update_brokerage(brokerage_id, brokerage_data)
    if updated_brokerage is None:
        raise NotFoundException(f"Brokerage with ID {brokerage_id} not found")
    return APIResponse.success_response(data=updated_brokerage, message="Brokerage updated successfully")

@router.delete("/{brokerage_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_brokerage(
    brokerage_id: str,
    brokerage_service: BrokerageService = Depends(),
    current_user: schemas.User = Depends(get_current_active_user) # Require auth to delete
):
    """
    Delete a brokerage.
    """
    deleted = await brokerage_service.delete_brokerage(brokerage_id)
    if not deleted:
        raise NotFoundException(f"Brokerage with ID {brokerage_id} not found")
    return None # Return None for 204 No Content 