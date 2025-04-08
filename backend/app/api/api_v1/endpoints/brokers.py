import logging
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, status

# Relative imports
from app import schemas
from app.services.broker_service import BrokerService
from app.db.neo4j_client import Neo4jClient
from app.utils.architecture import layer, ArchitectureLayer, log_cross_layer_call
from app.interfaces.api import ApiEndpoint
from app.core.exceptions import ValidationError, NotFoundException, StorageException
from app.core.dependencies import get_current_active_user # Assuming authentication is needed
from app.schemas.api import APIResponse

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/", response_model=APIResponse[List[schemas.Broker]])
@log_cross_layer_call(ArchitectureLayer.API, ArchitectureLayer.PROCESSING)
async def get_brokers(
    skip: int = 0,
    limit: int = 100,
    company: Optional[str] = Query(None, description="Filter by company name"),
    # service: BrokerService = Depends() # Example using DI if BrokerService is setup as dependency
):
    """
    Get all brokers with optional filtering and pagination.
    """
    # Assume service returns (items, total_count)
    broker_service = BrokerService() # Instantiate directly for now
    try:
        # TODO: Modify BrokerService.get_brokers to return total count for pagination
        brokers_data = await broker_service.get_brokers( # Assuming this just returns list for now
            skip=skip,
            limit=limit,
            company=company
        )
        total_count = len(brokers_data) # Placeholder: Get actual total count from service
        return APIResponse(
            data=brokers_data,
            meta={"total_count": total_count, "skip": skip, "limit": limit}
        )
    except StorageException as e:
        logger.error(f"Storage error fetching brokers: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to retrieve brokers")


@router.get("/{broker_id}", response_model=APIResponse[schemas.Broker])
# @layer(ArchitectureLayer.API) # Removed if not using class structure
async def get_broker(
    broker_id: str
    # service: BrokerService = Depends() # Example using DI
):
    """
    Get a specific broker by ID.
    """
    broker_service = BrokerService() # Instantiate directly for now
    try:
        broker_data = await broker_service.get_broker(broker_id)
        if broker_data is None:
            raise NotFoundException(f"Broker with id {broker_id} not found")
        return APIResponse(data=broker_data)
    except NotFoundException as e:
         raise e # Re-raise to be handled by exception handler
    except StorageException as e:
        logger.error(f"Storage error fetching broker {broker_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to retrieve broker")


@router.post("/", response_model=APIResponse[schemas.Broker], status_code=status.HTTP_201_CREATED)
async def create_broker(
    broker_data: schemas.BrokerCreate,
    user: schemas.User = Depends(get_current_active_user) # Added Auth Dependency
    # service: BrokerService = Depends() # Example using DI
):
    """
    Create a new broker. Requires authentication.
    """
    broker_service = BrokerService() # Instantiate directly for now
    try:
        new_broker = await broker_service.create_broker(broker_data)
        return APIResponse(data=new_broker)
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    except StorageException as e:
        logger.error(f"Storage error creating broker: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to create broker")


@router.put("/{broker_id}", response_model=APIResponse[schemas.Broker])
async def update_broker(
    broker_id: str,
    broker_data: schemas.BrokerUpdate,
    user: schemas.User = Depends(get_current_active_user) # Added Auth Dependency
    # service: BrokerService = Depends() # Example using DI
):
    """
    Update a broker. Requires authentication.
    """
    broker_service = BrokerService() # Instantiate directly for now
    try:
        updated_broker = await broker_service.update_broker(broker_id, broker_data)
        if updated_broker is None:
            raise NotFoundException(f"Broker with id {broker_id} not found for update")
        return APIResponse(data=updated_broker)
    except NotFoundException as e:
         raise e # Re-raise to be handled by exception handler
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    except StorageException as e:
        logger.error(f"Storage error updating broker {broker_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to update broker")


@router.delete("/{broker_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_broker(
    broker_id: str,
    user: schemas.User = Depends(get_current_active_user) # Added Auth Dependency
    # service: BrokerService = Depends() # Example using DI
):
    """
    Delete a broker. Requires authentication.
    """
    broker_service = BrokerService() # Instantiate directly for now
    try:
        deleted = await broker_service.delete_broker(broker_id)
        if not deleted:
            # Changed to raise NotFoundException
            raise NotFoundException(f"Broker with id {broker_id} not found for deletion")
        # Return None implicitly for 204
    except NotFoundException as e:
         raise e # Re-raise to be handled by exception handler
    except StorageException as e:
        logger.error(f"Storage error deleting broker {broker_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to delete broker")


# --- Neo4j Network Endpoint ---
# This endpoint remains largely unchanged as it uses a different client and has specific logic
# Consider refactoring Neo4jClient instantiation if using DI

from app.db.neo4j_client import Neo4jClient # Moved import closer to usage

@router.get("/{broker_id}/network", response_model=APIResponse[List[Dict[str, Any]]]) # Changed response model
async def get_broker_network(
    broker_id: str,
    depth: int = Query(2, description="Depth of the network to explore"),
    min_connections: int = Query(1, description="Minimum number of connections to include"),
    # service: BrokerService = Depends() # Example using DI
    # neo4j_client: Neo4jClient = Depends() # Example using DI for Neo4j
):
    """
    Get the network of brokers connected to a specific broker through common properties.
    Requires authentication. Uses Neo4j.
    """
    broker_service = BrokerService() # Instantiate directly for now
    # Check if the broker exists using the regular service
    try:
        broker_exists = await broker_service.get_broker(broker_id)
        if broker_exists is None:
            raise NotFoundException(f"Broker with id {broker_id} not found")
    except NotFoundException as e:
         raise e # Re-raise to be handled by exception handler
    except StorageException as e:
        logger.error(f"Storage error checking broker {broker_id} existence: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed checking broker existence")

    # Use Neo4j client to find the broker network
    neo4j_client = Neo4jClient() # Instantiate directly for now
    try:
        # Query remains the same as before...
        query = """
        MATCH (b1:Broker {id: $broker_id})

        // Find brokers connected through common properties
        OPTIONAL MATCH (b1)<-[:LISTED_BY]-(p:Property)-[:LISTED_BY]->(b2:Broker)
        WHERE b1 <> b2

        // Find brokers from the same company
        OPTIONAL MATCH (b3:Broker)
        WHERE b3.id <> b1.id
        AND b3.company = b1.company
        AND b3.company IS NOT NULL AND b3.company <> "" // Added null check

        // Combine results, removing duplicates
        WITH b1, collect(distinct b2) + collect(distinct b3) as direct_connections

        // If depth > 1, explore connections of connections
        OPTIONAL MATCH (b1)<-[:LISTED_BY]-(:Property)-[:LISTED_BY]->(direct:Broker)<-[:LISTED_BY]-(:Property)-[:LISTED_BY]->(indirect:Broker)
        WHERE b1 <> indirect
        AND NOT indirect IN direct_connections
        AND $depth > 1

        // Combine all connections
        WITH b1, direct_connections + collect(distinct indirect) as all_connections
        UNWIND all_connections as connected

        // Calculate connection strength
        OPTIONAL MATCH (b1)<-[:LISTED_BY]-(p1:Property)
        OPTIONAL MATCH (connected)<-[:LISTED_BY]-(p2:Property)
        WITH b1, connected,
             size(collect(distinct p1)) as b1_properties, // Use distinct properties
             size(collect(distinct p2)) as connected_properties, // Use distinct properties
             size([(b1)<-[:LISTED_BY]-(p:Property)-[:LISTED_BY]->(connected) | p]) as common_properties

        // Calculate connection score based on common properties and company
        WITH b1, connected, common_properties, b1_properties, connected_properties,
             CASE
                WHEN connected.company = b1.company AND connected.company IS NOT NULL AND connected.company <> "" THEN 3
                ELSE 0
             END as company_score,
             CASE
                WHEN common_properties > 5 THEN 5
                WHEN common_properties > 0 THEN common_properties
                ELSE 0
             END as property_score
        WITH connected, common_properties, connected_properties, (company_score + property_score) as connection_score

        // Filter by minimum connections
        WHERE connection_score >= $min_connections

        // Return results ordered by connection strength
        RETURN connected { .*, properties_count: connected_properties } as broker, // Include property count in broker data
               connection_score,
               common_properties
        ORDER BY connection_score DESC
        LIMIT 100 // Add a limit to prevent excessive results
        """

        results = neo4j_client.execute_query(query, {
            "broker_id": broker_id,
            "depth": depth,
            "min_connections": min_connections
        })

        # Format the results for APIResponse
        network_data = []
        for result in results:
            broker_node = result["broker"]
            # Convert Neo4j node properties to dict, handle potential missing keys safely
            broker_dict = {k: str(v) if v is not None else None for k, v in broker_node.items()}

            network_data.append({
                "broker": broker_dict,
                "connection_score": result.get("connection_score"),
                "common_properties": result.get("common_properties"),
                # total_properties is now included in broker_dict as properties_count
            })

        return APIResponse(data=network_data) # Wrap in APIResponse
    except Exception as e: # Catch broader exceptions for Neo4j query
        logger.error(f"Error querying Neo4j for broker {broker_id} network: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to retrieve broker network")
    finally:
        neo4j_client.close() 