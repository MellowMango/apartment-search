#!/usr/bin/env python3
"""
Property class for standardizing property data structure across scrapers.
"""

from typing import Dict, Any, Optional


class Property:
    """Class representing a property listing with standardized fields."""
    
    def __init__(
        self,
        id: str,
        title: str,
        description: str = "",
        location: str = "",
        price: str = "",
        url: str = "",
        broker: str = "",
        broker_url: str = "",
        units: str = "",
        sqft: str = "",
        year_built: str = "",
        status: str = "Available",
        additional_data: Dict[str, Any] = None
    ):
        """
        Initialize a property object with standardized fields.
        
        Args:
            id: Unique identifier for the property
            title: Title or name of the property
            description: Description of the property
            location: Location/address of the property
            price: Price of the property (as a string to preserve formatting)
            url: URL to the property listing
            broker: Name of the broker/source
            broker_url: URL of the broker/source
            units: Number of units (for multi-family properties)
            sqft: Square footage
            year_built: Year the property was built
            status: Status of the property (Available, Pending, Sold, etc.)
            additional_data: Dictionary of additional property-specific data
        """
        self.id = id
        self.title = title
        self.description = description
        self.location = location
        self.price = price
        self.url = url
        self.broker = broker
        self.broker_url = broker_url
        self.units = units
        self.sqft = sqft
        self.year_built = year_built
        self.status = status
        self.additional_data = additional_data or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert property object to a dictionary.
        
        Returns:
            Dictionary representation of the property
        """
        property_dict = {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "location": self.location,
            "price": self.price,
            "url": self.url,
            "broker": self.broker,
            "broker_url": self.broker_url,
            "units": self.units,
            "sqft": self.sqft,
            "year_built": self.year_built,
            "status": self.status,
        }
        
        # Add any additional data
        property_dict.update(self.additional_data)
        
        return property_dict
        
    def __str__(self) -> str:
        """String representation of the property."""
        return f"{self.title} - {self.location} - {self.price}" 