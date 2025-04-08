import logging
from datetime import datetime
from typing import Any, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

# Relative imports
from ....schemas import Property, PropertyCreate, PropertyUpdate
from ....services.property_service import PropertyService
from ....core.dependencies import get_current_active_user
from ....utils.architecture import ArchitectureLayer, layer, log_cross_layer_call
from ....interfaces.api import ApiEndpoint
from ....schemas import User
from ....core.config import settings
from ....interfaces.storage import PaginationParams, QueryResult
from ....schemas.api import APIResponse
from ....core.exceptions import (
    NotFoundException,
    StorageException,
    ValidationError,
)
# Removed Neo4jClient import as it wasn't used

logger = logging.getLogger(__name__)

router = APIRouter()

# Instantiate service here or use Depends() directly in endpoints
# Using Depends() is generally preferred for testability and dependency injection
# property_service = PropertyService()

# This module uses function-based endpoints with FastAPI,
# but we'll tag the key functions with their architectural layer

@layer(ArchitectureLayer.API)
class PropertiesEndpoint(ApiEndpoint):
    @router.get("/", response_model=APIResponse[List[Property]])
    @log_cross_layer_call(ArchitectureLayer.API, ArchitectureLayer.PROCESSING)
    async def get_properties(
        skip: int = 0,
        limit: int = 100,
        status_filter: Optional[str] = Query(None, alias="status", description="Filter by property status"), # Renamed status to status_filter to avoid conflict
        min_units: Optional[int] = Query(None, description="Minimum number of units"),
        max_units: Optional[int] = Query(None, description="Maximum number of units"),
        min_year_built: Optional[int] = Query(None, description="Minimum year built"),
        max_year_built: Optional[int] = Query(None, description="Maximum year built"),
        brokerage: Optional[str] = Query(None, description="Filter by brokerage"),
        property_service: PropertyService = Depends() # Use Depends for service
    ):
        """
        Get all properties with optional filtering.

        Returns:
            Standardized API response with paginated property data
        """
        try:
            # Validate input parameters (moved inside try block)
            if skip < 0:
                raise ValidationError(
                    message="Skip parameter must be non-negative",
                    field="skip"
                )

            if limit < 1 or limit > 1000: # Consider making max limit configurable
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
            # TODO: Update if property_service returns QueryResult for accurate total_count
            properties_result = await property_service.get_properties(
                skip=skip,
                limit=limit,
                status=status_filter, # Use renamed variable
                min_units=min_units,
                max_units=max_units,
                min_year_built=min_year_built,
                max_year_built=max_year_built,
                brokerage=brokerage
            )

            # Assuming properties_result is currently a List[Property]
            # If it becomes a QueryResult, adjust accordingly:
            # properties = properties_result.data
            # total_count = properties_result.total_count
            properties = properties_result # Assuming list for now
            total_count = len(properties) + skip  # Placeholder approximation

            # Create page number (1-based)
            page = (skip // limit) + 1 if limit > 0 else 1

            return APIResponse.paginated_response(
                data=properties,
                page=page,
                page_size=limit,
                total_items=total_count, # Use calculated total_count
                message="Properties retrieved successfully",
                meta={
                    "filters": {
                        "status": status_filter,
                        "min_units": min_units,
                        "max_units": max_units,
                        "min_year_built": min_year_built,
                        "max_year_built": max_year_built,
                        "brokerage": brokerage
                    }
                }
            )

        except ValidationError as e:
            # Let middleware handle validation errors
            raise
        except StorageException as e:
            # Let middleware handle storage errors
            raise
        except Exception as e:
            # Log unexpected errors
            logger.exception(f"Unexpected error in get_properties: {str(e)}")
            # Return a generic storage exception
            raise StorageException(
                message="An unexpected error occurred while retrieving properties.",
                details={"error": str(e)}
            )

    @router.get("/{property_id}", response_model=APIResponse[Property])
    async def get_property(
        property_id: str, # Consider using UUID type hint if IDs are UUIDs
        property_service: PropertyService = Depends() # Use Depends for service
    ):
        """
        Get a specific property by ID.

        Returns:
            Standardized API response with property data
        """
        try:
            # Basic ID validation (could be more specific, e.g., UUID validation)
            if not property_id:
                 raise ValidationError(message="Property ID cannot be empty", field="property_id")

            # Get property using service
            property_data = await property_service.get_property(property_id)

            # Handle not found case (service should raise NotFoundException)
            # If property_data is None (re-raise as NotFoundException if service doesn't)
            if property_data is None:
                 raise NotFoundException(f"Property with ID '{property_id}' not found.")

            # Return success response
            return APIResponse.success_response(
                data=property_data,
                message="Property retrieved successfully",
                meta={"property_id": property_id}
            )

        except (ValidationError, NotFoundException) as e:
            # Let middleware handle known exceptions
            raise
        except StorageException as e:
             # Let middleware handle storage errors
            raise
        except Exception as e:
            # Log unexpected errors
            logger.exception(f"Unexpected error retrieving property '{property_id}': {str(e)}")
            raise StorageException(
                message=f"An unexpected error occurred while retrieving property '{property_id}'.",
                details={"property_id": property_id, "error": str(e)}
            )

    @router.post("/", status_code=status.HTTP_201_CREATED, response_model=APIResponse[Property])
    async def create_property(
        property_data: PropertyCreate,
        property_service: PropertyService = Depends(), # Use Depends for service
        current_user: User = Depends(get_current_active_user) # Add Auth dependency
    ):
        """
        Create a new property. Requires authentication.

        Returns:
            Standardized API response with created property data
        """
        try:
            # Pydantic handles most validation; add business logic validation if needed
            # Example: if not await some_business_rule(property_data):
            #    raise ValidationError(...)

            # Create property using service
            created_property = await property_service.create_property(property_data)

            # Check if creation was successful (optional, depends on service behavior)
            if created_property is None:
                 raise StorageException("Failed to create property, service returned None.")


            # Return success response
            return APIResponse.success_response(
                data=created_property,
                message="Property created successfully",
                status_code=status.HTTP_201_CREATED, # Explicitly set status code here
                meta={"property_id": getattr(created_property, "id", None)}
            )

        except ValidationError as e:
            # Let middleware handle validation errors
            raise
        except StorageException as e:
             # Let middleware handle storage errors
            raise
        except Exception as e:
            # Log unexpected errors
            logger.exception(f"Unexpected error creating property: {str(e)}")
            raise StorageException(
                message="An unexpected error occurred while creating the property.",
                details={"error": str(e)}
            )

    @router.put("/{property_id}", response_model=APIResponse[Property])
    async def update_property(
        property_id: str, # Consider UUID type hint
        property_data: PropertyUpdate,
        property_service: PropertyService = Depends(), # Use Depends for service
        current_user: User = Depends(get_current_active_user) # Add Auth dependency
    ):
        """
        Update an existing property. Requires authentication.

        Returns:
            Standardized API response with updated property data
        """
        try:
             # Pydantic handles validation of the update payload
            # Add business logic validation if needed

            updated_property = await property_service.update_property(property_id, property_data)

            # Handle not found case (service should raise NotFoundException)
            # If service returns None instead:
            if updated_property is None:
                raise NotFoundException(f"Property with ID '{property_id}' not found for update.")

            return APIResponse.success_response(
                data=updated_property,
                message="Property updated successfully",
                meta={"property_id": property_id}
            )

        except (ValidationError, NotFoundException) as e:
             # Let middleware handle known exceptions
            raise
        except StorageException as e:
             # Let middleware handle storage errors
            raise
        except Exception as e:
            logger.exception(f"Unexpected error updating property '{property_id}': {str(e)}")
            raise StorageException(
                message=f"An unexpected error occurred while updating property '{property_id}'.",
                details={"property_id": property_id, "error": str(e)}
            )


    @router.delete("/{property_id}", response_model=APIResponse[None])
    async def delete_property(
        property_id: str, # Consider UUID type hint
        property_service: PropertyService = Depends(), # Use Depends for service
        current_user: User = Depends(get_current_active_user) # Add Auth dependency
    ):
        """
        Delete a property by ID. Requires authentication.

        Returns:
            Standardized API response confirming deletion (status 200 OK with null data)
        """
        try:
            success = await property_service.delete_property(property_id)

            # Handle not found case (service should raise NotFoundException)
            # If service returns False instead:
            if not success:
                 raise NotFoundException(f"Property with ID '{property_id}' not found for deletion.")


            # Return success response with no data
            # Note: Returning 200 OK with a message is often more informative than 204 No Content
            return APIResponse.success_response(
                data=None,
                message=f"Property with ID '{property_id}' deleted successfully",
                meta={"property_id": property_id}
            )

        except NotFoundException as e:
            # Let middleware handle not found errors
            raise
        except StorageException as e:
             # Let middleware handle storage errors
            raise
        except Exception as e:
            logger.exception(f"Unexpected error deleting property '{property_id}': {str(e)}")
            raise StorageException(
                message=f"An unexpected error occurred while deleting property '{property_id}'.",
                details={"property_id": property_id, "error": str(e)}
            )


    # TODO: Review get_related_properties endpoint if it's still needed
    # It currently uses Neo4j directly which might bypass service logic
    # Needs APIResponse, standard exceptions, etc.
    # Commenting out for now as it wasn't part of the initial request and uses Neo4j directly
    # @router.get("/{property_id}/related", response_model=List[Property])
    # async def get_related_properties(
    #     property_id: str,
    #     max_distance: float = Query(1.0, description="Maximum distance in miles"),
    #     limit: int = Query(10, description="Maximum number of related properties to return"),
    #     property_service: PropertyService = Depends() # Keep Depends for consistency? Or remove if unused?
    # ):
    #     """
    #     Get properties geographically related to a given property using Neo4j spatial search.
    #     (Requires Neo4j with spatial capabilities configured)
    #     """
    #     # This endpoint might need significant review:
    #     # 1. Uses Neo4jClient directly - should this be in the service layer?
    #     # 2. Lacks standard APIResponse, error handling, validation
    #     # 3. Assumes Neo4j setup and spatial index exist.
    #
    #     # Placeholder implementation - requires Neo4jClient setup
    #     # neo4j_client = Neo4jClient() # Needs proper initialization
    #     # try:
    #     #     related_props = await neo4j_client.find_properties_near(property_id, max_distance, limit)
    #     #     if related_props is None: # Or handle errors from client
    #     #          raise NotFoundException(f"Could not find or process property '{property_id}' for related search.")
    #     #     # Convert Neo4j results to Property schema if necessary
    #     #     # return APIResponse.success_response(data=related_props, ...)
    #     #     return related_props # Returning raw list for now
    #     # except Exception as e:
    #     #     logger.exception(f"Error finding related properties for '{property_id}': {e}")
    #     #     # raise StorageException(...)
    #     #     raise HTTPException(status_code=500, detail="Failed to retrieve related properties")
    #     # finally:
    #     #     await neo4j_client.close() # Ensure client is closed
    #
    #     # Returning dummy data or raising NotImplementedError might be better for now
    #     logger.warning(f"get_related_properties endpoint for '{property_id}' needs implementation review.")
    #     raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Related properties endpoint not fully implemented")

# Ensure the router is included in the main API router (e.g., in app/api/api_v1/api.py) 