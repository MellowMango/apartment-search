from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Path, Body
from sqlalchemy.orm import Session

from ....db.session import get_db
from ....services.correction_service import CorrectionService
from ....core.auth import get_current_user, get_current_active_superuser
from ....schemas.correction import (
    CorrectionCreate,
    CorrectionReview,
    PropertyCorrectionResponse,
    PropertyCorrectionsListResponse,
    PendingCorrectionsCount
)
from ....schemas.user import User

router = APIRouter()


@router.post("/", response_model=PropertyCorrectionResponse)
def create_correction(
    *,
    db: Session = Depends(get_db),
    data: CorrectionCreate,
    current_user: Optional[User] = Depends(get_current_user)
) -> Any:
    """
    Create a new property correction.
    
    This endpoint allows users (authenticated or anonymous) to submit
    corrections for property listings.
    """
    correction_service = CorrectionService(db)
    
    # If user is authenticated, use their ID
    user_id = current_user.id if current_user else None
    
    try:
        correction = correction_service.create_correction(data, user_id)
        return correction
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating correction: {str(e)}")


@router.get("/", response_model=PropertyCorrectionsListResponse)
def get_corrections(
    *,
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    status: Optional[str] = Query(None),
    property_id: Optional[int] = Query(None),
    current_user: User = Depends(get_current_active_superuser)
) -> Any:
    """
    Get property corrections with filters.
    
    This endpoint is restricted to superusers (admins) only.
    """
    correction_service = CorrectionService(db)
    
    corrections, total = correction_service.get_corrections(
        skip=skip,
        limit=limit,
        status=status,
        property_id=property_id
    )
    
    return {
        "items": corrections,
        "total": total,
        "has_more": total > skip + len(corrections)
    }


@router.get("/pending-count", response_model=PendingCorrectionsCount)
def get_pending_corrections_count(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_superuser)
) -> Any:
    """
    Get the count of pending corrections.
    
    This endpoint is restricted to superusers (admins) only.
    """
    correction_service = CorrectionService(db)
    count = correction_service.get_pending_corrections_count()
    
    return {"count": count}


@router.get("/{correction_id}", response_model=PropertyCorrectionResponse)
def get_correction(
    *,
    db: Session = Depends(get_db),
    correction_id: int = Path(..., ge=1),
    current_user: User = Depends(get_current_active_superuser)
) -> Any:
    """
    Get a property correction by ID.
    
    This endpoint is restricted to superusers (admins) only.
    """
    correction_service = CorrectionService(db)
    correction = correction_service.get_correction_by_id(correction_id)
    
    if not correction:
        raise HTTPException(status_code=404, detail=f"Correction with ID {correction_id} not found")
    
    return correction


@router.post("/{correction_id}/review", response_model=PropertyCorrectionResponse)
def review_correction(
    *,
    db: Session = Depends(get_db),
    correction_id: int = Path(..., ge=1),
    review_data: CorrectionReview = Body(...),
    current_user: User = Depends(get_current_active_superuser)
) -> Any:
    """
    Review a property correction.
    
    This endpoint allows admins to review, approve, or reject property corrections.
    If approved, the changes will be applied to the property.
    
    This endpoint is restricted to superusers (admins) only.
    """
    correction_service = CorrectionService(db)
    
    try:
        correction = correction_service.review_correction(
            correction_id=correction_id,
            review_data=review_data,
            admin_id=current_user.id
        )
        return correction
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reviewing correction: {str(e)}")


@router.get("/property/{property_id}", response_model=PropertyCorrectionsListResponse)
def get_property_corrections(
    *,
    db: Session = Depends(get_db),
    property_id: int = Path(..., ge=1),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    current_user: User = Depends(get_current_active_superuser)
) -> Any:
    """
    Get corrections for a specific property.
    
    This endpoint is restricted to superusers (admins) only.
    """
    correction_service = CorrectionService(db)
    
    corrections, total = correction_service.get_property_corrections(
        property_id=property_id,
        skip=skip,
        limit=limit
    )
    
    return {
        "items": corrections,
        "total": total,
        "has_more": total > skip + len(corrections)
    } 