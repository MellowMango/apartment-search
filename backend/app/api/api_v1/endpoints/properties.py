from typing import List, Optional
from datetime import datetime
import logging
from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.schemas.property import Property, PropertyCreate, PropertyUpdate
from app.services.property_service import PropertyService
from app.db.neo4j_client import Neo4jClient
from backend.app.utils.architecture import layer, ArchitectureLayer, log_cross_layer_call
from backend.app.interfaces.api import ApiEndpoint

logger = logging.getLogger(__name__)

router = APIRouter()

# This module uses function-based endpoints with FastAPI,
# but we'll tag the key functions with their architectural layer

from backend.app.schemas.api import APIResponse
from backend.app.core.exceptions import ValidationError, NotFoundException, StorageException

@router.get("/")
@layer(ArchitectureLayer.API)
async def get_properties(
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = Query(None, description="Filter by property status"),
    min_units: Optional[int] = Query(None, description="Minimum number of units"),
    max_units: Optional[int] = Query(None, description="Maximum number of units"),
    min_year_built: Optional[int] = Query(None, description="Minimum year built"),
    max_year_built: Optional[int] = Query(None, description="Maximum year built"),
    brokerage: Optional[str] = Query(None, description="Filter by brokerage"),
    property_service: PropertyService = Depends()
):
    """
    Get all properties with optional filtering.
    
    Returns:
        Standardized API response with paginated property data
    """
    try:
        # Validate input parameters
        if skip < 0:
            raise ValidationError(
                message="Skip parameter must be non-negative",
                field="skip"
            )
            
        if limit < 1 or limit > 1000:
            raise ValidationError(
                message="Limit parameter must be between 1 and 1000",
                field="limit"
            )
            
        if min_units is not None and min_units < 0:
            raise ValidationError(
                message="Minimum units must be non-negative",
                field="min_units"
            )
            
        if max_units is not None and max_units < 0:
            raise ValidationError(
                message="Maximum units must be non-negative",
                field="max_units"
            )
            
        if min_year_built is not None and min_year_built < 1800:
            raise ValidationError(
                message="Minimum year built must be after 1800",
                field="min_year_built"
            )
            
        if max_year_built is not None and max_year_built > datetime.now().year + 5:
            raise ValidationError(
                message=f"Maximum year built cannot be more than 5 years in the future",
                field="max_year_built"
            )
            
        if min_units is not None and max_units is not None and min_units > max_units:
            raise ValidationError(
                message="Minimum units cannot be greater than maximum units",
                details={"min_units": min_units, "max_units": max_units}
            )
            
        if min_year_built is not None and max_year_built is not None and min_year_built > max_year_built:
            raise ValidationError(
                message="Minimum year built cannot be greater than maximum year built",
                details={"min_year_built": min_year_built, "max_year_built": max_year_built}
            )
        
        # Get properties using service
        properties = await property_service.get_properties(
            skip=skip,
            limit=limit,
            status=status,
            min_units=min_units,
            max_units=max_units,
            min_year_built=min_year_built,
            max_year_built=max_year_built,
            brokerage=brokerage
        )
        
        # Return paginated response
        # Calculate total count (this should ideally come from the service)
        # For now, we'll use a placeholder for total_count
        total_count = len(properties) + skip  # This is an approximation
        
        # Create page number (1-based)
        page = (skip // limit) + 1 if limit > 0 else 1
        
        return APIResponse.paginated_response(
            data=properties,
            page=page,
            page_size=limit,
            total_items=total_count,
            message="Properties retrieved successfully",
            meta={
                "filters": {
                    "status": status,
                    "min_units": min_units,
                    "max_units": max_units,
                    "min_year_built": min_year_built,
                    "max_year_built": max_year_built,
                    "brokerage": brokerage
                }
            }
        )
        
    except ValidationError as e:
        # ValidationError is handled by the exception handler middleware
        raise
        
    except Exception as e:
        # Log unexpected errors
        logger.exception(f"Unexpected error in get_properties: {str(e)}")
        raise StorageException(
            message="Failed to retrieve properties",
            details={"error": str(e)}
        )

@router.get("/{property_id}")
async def get_property(
    property_id: str,
    property_service: PropertyService = Depends()
):
    """
    Get a specific property by ID.
    
    Returns:
        Standardized API response with property data
    """
    try:
        # Validate ID format (basic validation)
        if not property_id or len(property_id) < 3:
            raise ValidationError(
                message="Invalid property ID format",
                field="property_id"
            )
        
        # Get property using service
        property_data = await property_service.get_property(property_id)
        
        # Handle not found case
        if property_data is None:
            raise NotFoundException(
                message=f"Property with ID {property_id} not found",
                details={"property_id": property_id}
            )
        
        # Return success response
        return APIResponse.success_response(
            data=property_data,
            message="Property retrieved successfully",
            meta={"property_id": property_id}
        )
        
    except (ValidationError, NotFoundException) as e:
        # These exceptions are handled by the exception handler middleware
        raise
        
    except Exception as e:
        # Log unexpected errors
        logger.exception(f"Unexpected error in get_property: {str(e)}")
        raise StorageException(
            message=f"Failed to retrieve property with ID {property_id}",
            details={"property_id": property_id, "error": str(e)}
        )

@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_property(
    property_data: PropertyCreate,
    property_service: PropertyService = Depends()
):
    """
    Create a new property.
    
    Returns:
        Standardized API response with created property data
    """
    try:
        # Validate property data
        # Note: Most validation should be handled by Pydantic model,
        # but we can add additional business rule validations here
        
        # Create property using service
        created_property = await property_service.create_property(property_data)
        
        # Return success response
        return APIResponse.success_response(
            data=created_property,
            message="Property created successfully",
            meta={"property_id": getattr(created_property, "id", None)}
        )
        
    except ValidationError as e:
        # Validation errors are handled by the exception handler middleware
        raise
        
    except Exception as e:
        # Log unexpected errors
        logger.exception(f"Unexpected error in create_property: {str(e)}")
        raise StorageException(
            message="Failed to create property",
            details={"error": str(e)}
        )

@router.put("/{property_id}", response_model=Property)
async def update_property(
    property_id: str,
    property_data: PropertyUpdate,
    property_service: PropertyService = Depends()
):
    """
    Update a property.
    """
    updated_property = await property_service.update_property(property_id, property_data)
    if updated_property is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Property not found"
        )
    return updated_property

@router.delete("/{property_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_property(
    property_id: str,
    property_service: PropertyService = Depends()
):
    """
    Delete a property.
    """
    deleted = await property_service.delete_property(property_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Property not found"
        )
    return None

@router.get("/{property_id}/related", response_model=List[Property])
async def get_related_properties(
    property_id: str,
    max_distance: float = Query(1.0, description="Maximum distance in miles"),
    limit: int = Query(10, description="Maximum number of related properties to return"),
    property_service: PropertyService = Depends()
):
    """
    Get properties related to a specific property based on:
    - Geographic proximity
    - Similar characteristics (units, year built, etc.)
    - Same broker or brokerage
    
    Uses Neo4j graph database for relationship queries.
    """
    # First check if the property exists
    property_data = await property_service.get_property(property_id)
    if property_data is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Property not found"
        )
    
    # Use Neo4j client to find related properties
    neo4j_client = Neo4jClient()
    try:
        # Query for related properties using multiple relationship types
        query = """
        MATCH (p:Property {id: $property_id})
        
        // Find properties with the same broker
        OPTIONAL MATCH (p)-[:LISTED_BY]->(b:Broker)<-[:LISTED_BY]-(similar:Property)
        
        // Find properties that are geographically close
        OPTIONAL MATCH (nearby:Property)
        WHERE nearby.id <> p.id
        AND nearby.id <> similar.id
        AND point.distance(
            point({latitude: p.latitude, longitude: p.longitude}),
            point({latitude: nearby.latitude, longitude: nearby.longitude})
        ) / 1609.34 < $max_distance  // Convert meters to miles
        
        // Combine results, removing duplicates
        WITH p, collect(distinct similar) + collect(distinct nearby) as related_properties
        UNWIND related_properties as related
        
        // Calculate a relevance score based on multiple factors
        WITH related, 
             CASE 
                WHEN exists((related)-[:LISTED_BY]->()<-[:LISTED_BY]-(p)) THEN 3  // Same broker
                ELSE 0
             END +
             CASE 
                WHEN abs(related.year_built - p.year_built) < 5 THEN 2  // Similar age
                WHEN abs(related.year_built - p.year_built) < 10 THEN 1
                ELSE 0
             END +
             CASE 
                WHEN abs(related.units - p.units) < 5 THEN 2  // Similar size
                WHEN abs(related.units - p.units) < 10 THEN 1
                ELSE 0
             END +
             CASE 
                WHEN related.property_type = p.property_type THEN 2  // Same property type
                ELSE 0
             END +
             CASE 
                WHEN point.distance(
                    point({latitude: p.latitude, longitude: p.longitude}),
                    point({latitude: related.latitude, longitude: related.longitude})
                ) / 1609.34 < 0.5 THEN 3  // Very close (< 0.5 miles)
                WHEN point.distance(
                    point({latitude: p.latitude, longitude: p.longitude}),
                    point({latitude: related.latitude, longitude: related.longitude})
                ) / 1609.34 < 1.0 THEN 2  // Close (< 1 mile)
                ELSE 1
             END as relevance_score
        
        // Return results ordered by relevance
        RETURN related, relevance_score
        ORDER BY relevance_score DESC
        LIMIT $limit
        """
        
        results = neo4j_client.execute_query(query, {
            "property_id": property_id,
            "max_distance": max_distance,
            "limit": limit
        })
        
        # Convert Neo4j nodes to Property objects
        related_properties = []
        for result in results:
            property_node = result["related"]
            # Convert Neo4j node to dict and create Property object
            property_dict = dict(property_node)
            # Convert datetime objects to strings if needed
            if "created_at" in property_dict and property_dict["created_at"]:
                property_dict["created_at"] = str(property_dict["created_at"])
            if "updated_at" in property_dict and property_dict["updated_at"]:
                property_dict["updated_at"] = str(property_dict["updated_at"])
            
            related_properties.append(Property(**property_dict))
        
        return related_properties
    finally:
        neo4j_client.close() 