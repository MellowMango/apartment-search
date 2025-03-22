from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from ..db.base_class import Base


class PropertyCorrection(Base):
    """
    Model for user-submitted property corrections.
    
    This model stores corrections submitted by users for properties with missing
    or incorrect information. Each correction is reviewed by admins before being
    applied to the property.
    """
    __tablename__ = "property_corrections"

    id = Column(Integer, primary_key=True, index=True)
    property_id = Column(Integer, ForeignKey("properties.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Fields that were corrected
    corrected_fields = Column(JSON, nullable=False)
    
    # Original and updated values in JSON format
    original_values = Column(JSON, nullable=True)
    updated_values = Column(JSON, nullable=False)
    
    # Correction submission details
    submission_notes = Column(Text, nullable=True)
    submitter_email = Column(String, nullable=True)
    submitter_name = Column(String, nullable=True)
    submission_date = Column(DateTime(timezone=True), server_default=func.now())
    
    # Review details
    status = Column(String, nullable=False, default="pending")  # pending, approved, rejected
    reviewed_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    review_date = Column(DateTime(timezone=True), nullable=True)
    review_notes = Column(Text, nullable=True)
    
    # Applied details
    applied = Column(Boolean, default=False)
    applied_date = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    property = relationship("Property", back_populates="corrections")
    user = relationship("User", foreign_keys=[user_id], back_populates="submitted_corrections")
    reviewer = relationship("User", foreign_keys=[reviewed_by], back_populates="reviewed_corrections") 