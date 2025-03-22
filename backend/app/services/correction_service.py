from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func

from ..models.corrections import PropertyCorrection
from ..models.property import Property
from ..schemas.correction import CorrectionCreate, CorrectionReview
from ..core.logging import get_logger

logger = get_logger(__name__)


class CorrectionService:
    """Service for handling property corrections"""

    def __init__(self, db: Session):
        self.db = db

    def get_corrections(
        self,
        skip: int = 0,
        limit: int = 100,
        status: Optional[str] = None,
        property_id: Optional[int] = None,
        user_id: Optional[int] = None,
    ) -> Tuple[List[PropertyCorrection], int]:
        """
        Get property corrections with filters.
        
        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return
            status: Filter by correction status
            property_id: Filter by property ID
            user_id: Filter by submitter user ID
            
        Returns:
            Tuple of (corrections list, total count)
        """
        query = self.db.query(PropertyCorrection)
        
        # Apply filters
        if status:
            query = query.filter(PropertyCorrection.status == status)
        if property_id:
            query = query.filter(PropertyCorrection.property_id == property_id)
        if user_id:
            query = query.filter(PropertyCorrection.user_id == user_id)
            
        # Get total count
        total = query.count()
        
        # Apply pagination
        corrections = query.order_by(PropertyCorrection.submission_date.desc()) \
            .offset(skip).limit(limit).all()
            
        return corrections, total

    def get_correction_by_id(self, correction_id: int) -> Optional[PropertyCorrection]:
        """
        Get a property correction by ID.
        
        Args:
            correction_id: ID of the correction to retrieve
            
        Returns:
            PropertyCorrection object or None if not found
        """
        return self.db.query(PropertyCorrection).filter(
            PropertyCorrection.id == correction_id
        ).first()

    def create_correction(
        self, 
        data: CorrectionCreate, 
        user_id: Optional[int] = None
    ) -> PropertyCorrection:
        """
        Create a new property correction.
        
        Args:
            data: Correction data
            user_id: ID of the user submitting the correction (optional)
            
        Returns:
            Created PropertyCorrection object
        """
        # Check if property exists
        property_obj = self.db.query(Property).filter(
            Property.id == data.property_id
        ).first()
        
        if not property_obj:
            raise ValueError(f"Property with ID {data.property_id} not found")
        
        # Get original values
        original_values = {}
        for field in data.corrected_fields:
            if hasattr(property_obj, field):
                original_values[field] = getattr(property_obj, field)
        
        # Create correction
        correction = PropertyCorrection(
            property_id=data.property_id,
            user_id=user_id,
            corrected_fields=data.corrected_fields,
            original_values=original_values,
            updated_values=data.updated_values,
            submission_notes=data.submission_notes,
            submitter_email=data.submitter_email,
            submitter_name=data.submitter_name,
            status="pending"
        )
        
        self.db.add(correction)
        self.db.commit()
        self.db.refresh(correction)
        
        # Set property as needing review
        property_obj.needs_review = True
        self.db.commit()
        
        logger.info(f"Created property correction {correction.id} for property {property_obj.id}")
        
        return correction

    def review_correction(
        self, 
        correction_id: int, 
        review_data: CorrectionReview, 
        admin_id: int
    ) -> PropertyCorrection:
        """
        Review a property correction.
        
        Args:
            correction_id: ID of the correction to review
            review_data: Review data
            admin_id: ID of the admin reviewing the correction
            
        Returns:
            Updated PropertyCorrection object
        """
        correction = self.get_correction_by_id(correction_id)
        
        if not correction:
            raise ValueError(f"Correction with ID {correction_id} not found")
        
        # Update correction with review data
        correction.status = review_data.status
        correction.review_notes = review_data.review_notes
        correction.reviewed_by = admin_id
        correction.review_date = datetime.now()
        
        # If approved, apply changes to property
        if review_data.status == "approved":
            property_obj = self.db.query(Property).filter(
                Property.id == correction.property_id
            ).first()
            
            if property_obj:
                # Apply changes
                for field, value in correction.updated_values.items():
                    if hasattr(property_obj, field):
                        setattr(property_obj, field, value)
                
                # Mark property as verified and update timestamp
                property_obj.verified = True
                property_obj.needs_review = False
                property_obj.last_updated = datetime.now()
                
                # Mark correction as applied
                correction.applied = True
                correction.applied_date = datetime.now()
                
                logger.info(f"Applied correction {correction.id} to property {property_obj.id}")
            else:
                logger.error(f"Property {correction.property_id} not found when applying correction {correction.id}")
        
        # If rejected, just mark property as not needing review
        if review_data.status == "rejected":
            property_obj = self.db.query(Property).filter(
                Property.id == correction.property_id
            ).first()
            
            if property_obj:
                property_obj.needs_review = False
            
            logger.info(f"Rejected correction {correction.id} for property {correction.property_id}")
        
        self.db.commit()
        self.db.refresh(correction)
        
        return correction

    def get_pending_corrections_count(self) -> int:
        """
        Get the count of pending corrections.
        
        Returns:
            Count of pending corrections
        """
        return self.db.query(PropertyCorrection).filter(
            PropertyCorrection.status == "pending"
        ).count()

    def get_property_corrections(
        self, 
        property_id: int,
        skip: int = 0,
        limit: int = 100
    ) -> Tuple[List[PropertyCorrection], int]:
        """
        Get corrections for a specific property.
        
        Args:
            property_id: ID of the property
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            Tuple of (corrections list, total count)
        """
        query = self.db.query(PropertyCorrection).filter(
            PropertyCorrection.property_id == property_id
        )
        
        total = query.count()
        
        corrections = query.order_by(PropertyCorrection.submission_date.desc()) \
            .offset(skip).limit(limit).all()
        
        return corrections, total 