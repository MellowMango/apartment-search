from sqlalchemy import Boolean, Column, String, Integer, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from ..db.base_class import Base


class User(Base):
    """Database model for users"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    full_name = Column(String, nullable=True)
    phone_number = Column(String, nullable=True)
    hashed_password = Column(String, nullable=False)
    role = Column(String, default="user")  # user, admin, superuser
    
    # Verification
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    verification_token = Column(String, nullable=True)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_login = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    subscriptions = relationship("Subscription", back_populates="user")
    submitted_corrections = relationship("PropertyCorrection", foreign_keys="PropertyCorrection.user_id", back_populates="user")
    reviewed_corrections = relationship("PropertyCorrection", foreign_keys="PropertyCorrection.reviewed_by", back_populates="reviewer") 