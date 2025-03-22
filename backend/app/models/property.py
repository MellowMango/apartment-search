from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from ..db.base_class import Base


class Property(Base):
    """Database model for properties"""
    __tablename__ = "properties"

    id = Column(Integer, primary_key=True, index=True)
    
    # Basic property info
    property_name = Column(String, index=True)
    address = Column(String, index=True)
    city = Column(String, index=True)
    state = Column(String, index=True)
    zip_code = Column(String, index=True)
    
    # Location coordinates
    latitude = Column(Float, index=True)
    longitude = Column(Float, index=True)
    
    # Property details
    property_type = Column(String, index=True)  # multifamily, commercial, mixed-use, etc.
    units_count = Column(Integer, nullable=True)
    year_built = Column(Integer, nullable=True)
    square_footage = Column(Float, nullable=True)
    lot_size = Column(Float, nullable=True)
    zoning = Column(String, nullable=True)
    
    # Pricing and financials
    price = Column(Float, nullable=True)
    price_per_unit = Column(Float, nullable=True)
    cap_rate = Column(Float, nullable=True)
    noi = Column(Float, nullable=True)  # Net Operating Income
    occupancy_rate = Column(Float, nullable=True)
    
    # Features and amenities
    parking_spaces = Column(Integer, nullable=True)
    amenities = Column(JSON, nullable=True)  # List of amenities as JSON
    description = Column(Text, nullable=True)
    
    # Listing status
    status = Column(String, index=True, default="active")  # active, under contract, sold, etc.
    listing_date = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    broker_id = Column(Integer, ForeignKey("brokers.id"), nullable=True)
    broker = relationship("Broker", back_populates="properties")
    
    # Images (one-to-many)
    images = relationship("PropertyImage", back_populates="property", cascade="all, delete-orphan")
    
    # Corrections (one-to-many)
    corrections = relationship("PropertyCorrection", back_populates="property", cascade="all, delete-orphan")
    
    # Source and metadata
    source = Column(String, nullable=True)  # source of the listing, e.g., website, MLS, etc.
    source_id = Column(String, nullable=True)  # original ID from the source
    source_url = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_updated = Column(DateTime(timezone=True), server_default=func.now())
    
    # Data quality
    geocoded = Column(Boolean, default=False)
    verified = Column(Boolean, default=False)
    needs_review = Column(Boolean, default=False)


class PropertyImage(Base):
    """Database model for property images"""
    __tablename__ = "property_images"
    
    id = Column(Integer, primary_key=True, index=True)
    property_id = Column(Integer, ForeignKey("properties.id"))
    url = Column(String, nullable=False)
    caption = Column(String, nullable=True)
    order = Column(Integer, default=0)
    
    # Relationships
    property = relationship("Property", back_populates="images") 