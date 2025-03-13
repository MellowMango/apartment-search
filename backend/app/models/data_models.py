"""
Data Models for Austin Multifamily Property Listing Map

This file defines the data models used in both Supabase (PostgreSQL) and Neo4j.
It serves as a reference for the fields and relationships between entities.

The models are designed to ensure synergy between the relational database (Supabase)
and the graph database (Neo4j), allowing for efficient data synchronization and querying.
"""

from typing import Dict, List, Optional, Any, TypedDict
from datetime import datetime
from enum import Enum


# Enums for standardized values
class PropertyStatus(str, Enum):
    ACTIVE = "active"
    UNDER_CONTRACT = "under_contract"
    SOLD = "sold"
    OFF_MARKET = "off_market"
    COMING_SOON = "coming_soon"


class PropertyType(str, Enum):
    MULTIFAMILY = "multifamily"
    MIXED_USE = "mixed_use"
    STUDENT_HOUSING = "student_housing"
    SENIOR_HOUSING = "senior_housing"
    AFFORDABLE_HOUSING = "affordable_housing"


class RelationshipType(str, Enum):
    LISTS = "LISTS"  # Broker lists Property
    BELONGS_TO = "BELONGS_TO"  # Broker belongs to Brokerage
    WORKS_WITH = "WORKS_WITH"  # Broker works with Broker
    NEAR = "NEAR"  # Property is near Property
    SIMILAR_TO = "SIMILAR_TO"  # Property is similar to Property
    REPRESENTS = "REPRESENTS"  # Brokerage represents Property
    COMPETES_WITH = "COMPETES_WITH"  # Brokerage competes with Brokerage


# TypedDict models for Supabase (PostgreSQL)
class PropertyDict(TypedDict, total=False):
    """
    Property model for Supabase (PostgreSQL)
    
    This represents a multifamily property listing in the database.
    """
    id: str  # UUID
    name: str  # Property name
    address: str  # Street address
    city: str  # City (default: Austin)
    state: str  # State (default: TX)
    zip_code: Optional[str]  # ZIP code
    latitude: Optional[float]  # Latitude coordinate
    longitude: Optional[float]  # Longitude coordinate
    price: Optional[float]  # Asking price
    units: Optional[int]  # Number of units
    year_built: Optional[int]  # Year built
    year_renovated: Optional[int]  # Year renovated
    square_feet: Optional[float]  # Total square footage
    price_per_unit: Optional[float]  # Price per unit
    price_per_sqft: Optional[float]  # Price per square foot
    cap_rate: Optional[float]  # Capitalization rate
    property_type: Optional[str]  # Type of property (see PropertyType enum)
    property_status: str  # Status (see PropertyStatus enum)
    property_website: Optional[str]  # Property website URL
    listing_website: Optional[str]  # Listing website URL
    call_for_offers_date: Optional[datetime]  # Deadline for offers
    description: Optional[str]  # Property description
    amenities: Optional[Dict[str, Any]]  # JSON of amenities
    images: Optional[List[str]]  # JSON array of image URLs
    broker_id: Optional[str]  # UUID of listing broker
    brokerage_id: Optional[str]  # UUID of listing brokerage
    created_at: datetime  # Record creation timestamp
    updated_at: datetime  # Record update timestamp
    date_first_appeared: datetime  # When property first appeared


class BrokerDict(TypedDict, total=False):
    """
    Broker model for Supabase (PostgreSQL)
    
    This represents a real estate broker in the database.
    """
    id: str  # UUID
    name: str  # Broker name
    company: Optional[str]  # Company name (if different from brokerage)
    email: Optional[str]  # Email address
    phone: Optional[str]  # Phone number
    website: Optional[str]  # Personal website URL
    brokerage_id: Optional[str]  # UUID of associated brokerage
    created_at: datetime  # Record creation timestamp
    updated_at: datetime  # Record update timestamp


class BrokerageDict(TypedDict, total=False):
    """
    Brokerage model for Supabase (PostgreSQL)
    
    This represents a real estate brokerage firm in the database.
    """
    id: str  # UUID
    name: str  # Brokerage name
    website: Optional[str]  # Website URL
    logo_url: Optional[str]  # Logo image URL
    address: Optional[str]  # Street address
    city: str  # City (default: Austin)
    state: str  # State (default: TX)
    zip_code: Optional[str]  # ZIP code
    created_at: datetime  # Record creation timestamp
    updated_at: datetime  # Record update timestamp


class UserProfileDict(TypedDict, total=False):
    """
    User Profile model for Supabase (PostgreSQL)
    
    This represents a user of the application.
    """
    id: str  # UUID (matches auth.users.id)
    email: str  # Email address
    first_name: Optional[str]  # First name
    last_name: Optional[str]  # Last name
    company: Optional[str]  # Company name
    phone: Optional[str]  # Phone number
    role: str  # User role (user, admin)
    is_active: bool  # Whether user is active
    subscription_id: Optional[str]  # UUID of active subscription
    created_at: datetime  # Record creation timestamp
    updated_at: datetime  # Record update timestamp


class SubscriptionDict(TypedDict, total=False):
    """
    Subscription model for Supabase (PostgreSQL)
    
    This represents a user's subscription to the service.
    """
    id: str  # UUID
    user_id: str  # UUID of user
    stripe_customer_id: str  # Stripe customer ID
    stripe_subscription_id: str  # Stripe subscription ID
    plan_type: str  # Subscription plan type (monthly, annual)
    status: str  # Subscription status
    current_period_start: datetime  # Start of current billing period
    current_period_end: datetime  # End of current billing period
    created_at: datetime  # Record creation timestamp
    updated_at: datetime  # Record update timestamp


class SavedPropertyDict(TypedDict, total=False):
    """
    Saved Property model for Supabase (PostgreSQL)
    
    This represents a property saved by a user.
    """
    id: str  # UUID
    user_id: str  # UUID of user
    property_id: str  # UUID of property
    created_at: datetime  # Record creation timestamp


class PropertyNoteDict(TypedDict, total=False):
    """
    Property Note model for Supabase (PostgreSQL)
    
    This represents a note added by a user to a property.
    """
    id: str  # UUID
    user_id: str  # UUID of user
    property_id: str  # UUID of property
    content: str  # Note content
    created_at: datetime  # Record creation timestamp
    updated_at: datetime  # Record update timestamp


# Neo4j Node and Relationship Models
class Neo4jPropertyNode(TypedDict, total=False):
    """
    Property Node model for Neo4j
    
    This represents a property node in the graph database.
    """
    id: str  # UUID (same as Supabase)
    name: str  # Property name
    address: str  # Street address
    city: str  # City
    state: str  # State
    zip_code: Optional[str]  # ZIP code
    latitude: Optional[float]  # Latitude coordinate
    longitude: Optional[float]  # Longitude coordinate
    price: Optional[float]  # Asking price
    units: Optional[int]  # Number of units
    year_built: Optional[int]  # Year built
    square_feet: Optional[float]  # Total square footage
    price_per_unit: Optional[float]  # Price per unit
    property_type: Optional[str]  # Type of property
    property_status: str  # Status
    created_at: datetime  # Creation timestamp
    updated_at: datetime  # Update timestamp


class Neo4jBrokerNode(TypedDict, total=False):
    """
    Broker Node model for Neo4j
    
    This represents a broker node in the graph database.
    """
    id: str  # UUID (same as Supabase)
    name: str  # Broker name
    company: Optional[str]  # Company name
    email: Optional[str]  # Email address
    phone: Optional[str]  # Phone number
    website: Optional[str]  # Website URL
    created_at: datetime  # Creation timestamp
    updated_at: datetime  # Update timestamp


class Neo4jBrokerageNode(TypedDict, total=False):
    """
    Brokerage Node model for Neo4j
    
    This represents a brokerage node in the graph database.
    """
    id: str  # UUID (same as Supabase)
    name: str  # Brokerage name
    website: Optional[str]  # Website URL
    city: str  # City
    state: str  # State
    created_at: datetime  # Creation timestamp
    updated_at: datetime  # Update timestamp


class Neo4jRelationship(TypedDict, total=False):
    """
    Relationship model for Neo4j
    
    This represents a relationship between nodes in the graph database.
    """
    type: str  # Relationship type (see RelationshipType enum)
    from_id: str  # UUID of source node
    to_id: str  # UUID of target node
    properties: Dict[str, Any]  # Additional relationship properties


# Cypher Queries for Neo4j Graph Database

# Create Property Node
CREATE_PROPERTY_NODE = """
MERGE (p:Property {id: $id})
ON CREATE SET
    p.name = $name,
    p.address = $address,
    p.city = $city,
    p.state = $state,
    p.zip_code = $zip_code,
    p.latitude = $latitude,
    p.longitude = $longitude,
    p.price = $price,
    p.units = $units,
    p.year_built = $year_built,
    p.square_feet = $square_feet,
    p.price_per_unit = $price_per_unit,
    p.property_type = $property_type,
    p.property_status = $property_status,
    p.created_at = datetime($created_at),
    p.updated_at = datetime($updated_at)
ON MATCH SET
    p.name = $name,
    p.address = $address,
    p.city = $city,
    p.state = $state,
    p.zip_code = $zip_code,
    p.latitude = $latitude,
    p.longitude = $longitude,
    p.price = $price,
    p.units = $units,
    p.year_built = $year_built,
    p.square_feet = $square_feet,
    p.price_per_unit = $price_per_unit,
    p.property_type = $property_type,
    p.property_status = $property_status,
    p.updated_at = datetime($updated_at)
RETURN p
"""

# Create Broker Node
CREATE_BROKER_NODE = """
MERGE (b:Broker {id: $id})
ON CREATE SET
    b.name = $name,
    b.company = $company,
    b.email = $email,
    b.phone = $phone,
    b.website = $website,
    b.created_at = datetime($created_at),
    b.updated_at = datetime($updated_at)
ON MATCH SET
    b.name = $name,
    b.company = $company,
    b.email = $email,
    b.phone = $phone,
    b.website = $website,
    b.updated_at = datetime($updated_at)
RETURN b
"""

# Create Brokerage Node
CREATE_BROKERAGE_NODE = """
MERGE (b:Brokerage {id: $id})
ON CREATE SET
    b.name = $name,
    b.website = $website,
    b.city = $city,
    b.state = $state,
    b.created_at = datetime($created_at),
    b.updated_at = datetime($updated_at)
ON MATCH SET
    b.name = $name,
    b.website = $website,
    b.city = $city,
    b.state = $state,
    b.updated_at = datetime($updated_at)
RETURN b
"""

# Link Broker to Property (LISTS relationship)
LINK_BROKER_TO_PROPERTY = """
MATCH (b:Broker {id: $broker_id})
MATCH (p:Property {id: $property_id})
MERGE (b)-[r:LISTS]->(p)
RETURN b, r, p
"""

# Link Broker to Brokerage (BELONGS_TO relationship)
LINK_BROKER_TO_BROKERAGE = """
MATCH (b:Broker {id: $broker_id})
MATCH (br:Brokerage {id: $brokerage_id})
MERGE (b)-[r:BELONGS_TO]->(br)
RETURN b, r, br
"""

# Link Brokerage to Property (REPRESENTS relationship)
LINK_BROKERAGE_TO_PROPERTY = """
MATCH (br:Brokerage {id: $brokerage_id})
MATCH (p:Property {id: $property_id})
MERGE (br)-[r:REPRESENTS]->(p)
RETURN br, r, p
"""

# Find Similar Properties (based on location, price, units)
FIND_SIMILAR_PROPERTIES = """
MATCH (p:Property {id: $property_id})
MATCH (other:Property)
WHERE other.id <> $property_id
  AND other.city = p.city
  AND other.property_type = p.property_type
  AND abs(other.price - p.price) / p.price < 0.2
  AND abs(other.units - p.units) / p.units < 0.2
MERGE (p)-[r:SIMILAR_TO {
    price_diff: abs(other.price - p.price) / p.price,
    units_diff: abs(other.units - p.units) / p.units
}]->(other)
RETURN p, r, other
"""

# Find Nearby Properties (based on geographic coordinates)
FIND_NEARBY_PROPERTIES = """
MATCH (p:Property {id: $property_id})
MATCH (other:Property)
WHERE other.id <> $property_id
  AND other.latitude IS NOT NULL
  AND other.longitude IS NOT NULL
  AND p.latitude IS NOT NULL
  AND p.longitude IS NOT NULL
  AND point.distance(
    point({latitude: p.latitude, longitude: p.longitude}),
    point({latitude: other.latitude, longitude: other.longitude})
  ) < 1000  // Within 1km
MERGE (p)-[r:NEAR {
    distance: point.distance(
      point({latitude: p.latitude, longitude: p.longitude}),
      point({latitude: other.latitude, longitude: other.longitude})
    )
}]->(other)
RETURN p, r, other
"""

# Find Broker Network (brokers who work with the same properties)
FIND_BROKER_NETWORK = """
MATCH (b:Broker {id: $broker_id})
MATCH (b)-[:LISTS]->(p:Property)<-[:LISTS]-(other:Broker)
WHERE other.id <> $broker_id
WITH b, other, count(p) AS shared_properties
WHERE shared_properties > 0
MERGE (b)-[r:WORKS_WITH {shared_properties: shared_properties}]->(other)
RETURN b, r, other
"""

# Find Competing Brokerages (brokerages with properties in the same areas)
FIND_COMPETING_BROKERAGES = """
MATCH (br:Brokerage {id: $brokerage_id})
MATCH (br)-[:REPRESENTS]->(p:Property)
MATCH (other:Brokerage)-[:REPRESENTS]->(op:Property)
WHERE other.id <> $brokerage_id
  AND op.city = p.city
  AND op.property_type = p.property_type
WITH br, other, count(DISTINCT p) AS area_overlap
WHERE area_overlap > 0
MERGE (br)-[r:COMPETES_WITH {area_overlap: area_overlap}]->(other)
RETURN br, r, other
""" 