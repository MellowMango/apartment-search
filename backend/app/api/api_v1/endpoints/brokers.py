from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.schemas.broker import Broker, BrokerCreate, BrokerUpdate
from app.services.broker_service import BrokerService
from app.db.neo4j_client import Neo4jClient
from backend.app.utils.architecture import layer, ArchitectureLayer, log_cross_layer_call
from backend.app.interfaces.api import ApiEndpoint

router = APIRouter()

@router.get("/", response_model=List[Broker])
@layer(ArchitectureLayer.API)
async def get_brokers(
    skip: int = 0,
    limit: int = 100,
    company: Optional[str] = Query(None, description="Filter by company name"),
    broker_service: BrokerService = Depends()
):
    """
    Get all brokers with optional filtering.
    """
    return await broker_service.get_brokers(
        skip=skip,
        limit=limit,
        company=company
    )

@router.get("/{broker_id}", response_model=Broker)
@layer(ArchitectureLayer.API)
async def get_broker(
    broker_id: str,
    broker_service: BrokerService = Depends()
):
    """
    Get a specific broker by ID.
    """
    broker_data = await broker_service.get_broker(broker_id)
    if broker_data is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Broker not found"
        )
    return broker_data

@router.post("/", response_model=Broker, status_code=status.HTTP_201_CREATED)
async def create_broker(
    broker_data: BrokerCreate,
    broker_service: BrokerService = Depends()
):
    """
    Create a new broker.
    """
    return await broker_service.create_broker(broker_data)

@router.put("/{broker_id}", response_model=Broker)
async def update_broker(
    broker_id: str,
    broker_data: BrokerUpdate,
    broker_service: BrokerService = Depends()
):
    """
    Update a broker.
    """
    updated_broker = await broker_service.update_broker(broker_id, broker_data)
    if updated_broker is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Broker not found"
        )
    return updated_broker

@router.delete("/{broker_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_broker(
    broker_id: str,
    broker_service: BrokerService = Depends()
):
    """
    Delete a broker.
    """
    deleted = await broker_service.delete_broker(broker_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Broker not found"
        )
    return None

@router.get("/{broker_id}/network", response_model=List[Dict[str, Any]])
async def get_broker_network(
    broker_id: str,
    depth: int = Query(2, description="Depth of the network to explore"),
    min_connections: int = Query(1, description="Minimum number of connections to include"),
    broker_service: BrokerService = Depends()
):
    """
    Get the network of brokers connected to a specific broker through common properties.
    
    This endpoint uses Neo4j graph database to find brokers that are connected through:
    - Properties listed by the same broker
    - Properties in the same area
    - Brokers that work for the same company
    
    The depth parameter controls how far to explore the network (e.g., brokers connected to connected brokers).
    """
    # First check if the broker exists
    broker_data = await broker_service.get_broker(broker_id)
    if broker_data is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Broker not found"
        )
    
    # Use Neo4j client to find the broker network
    neo4j_client = Neo4jClient()
    try:
        # Query for broker network
        query = """
        MATCH (b1:Broker {id: $broker_id})
        
        // Find brokers connected through common properties
        OPTIONAL MATCH (b1)<-[:LISTED_BY]-(p:Property)-[:LISTED_BY]->(b2:Broker)
        WHERE b1 <> b2
        
        // Find brokers from the same company
        OPTIONAL MATCH (b3:Broker)
        WHERE b3.id <> b1.id
        AND b3.company = b1.company
        AND b3.company <> ""
        
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
             size(collect(p1)) as b1_properties,
             size(collect(p2)) as connected_properties,
             size([(b1)<-[:LISTED_BY]-(p:Property)-[:LISTED_BY]->(connected) | p]) as common_properties
        
        // Calculate connection score based on common properties and company
        WITH connected, 
             CASE 
                WHEN connected.company = b1.company AND connected.company <> "" THEN 3
                ELSE 0
             END +
             CASE
                WHEN common_properties > 5 THEN 5
                WHEN common_properties > 0 THEN common_properties
                ELSE 0
             END as connection_score,
             common_properties,
             b1_properties,
             connected_properties
        
        // Filter by minimum connections
        WHERE connection_score >= $min_connections
        
        // Return results ordered by connection strength
        RETURN connected as broker, 
               connection_score,
               common_properties,
               connected_properties as total_properties
        ORDER BY connection_score DESC
        """
        
        results = neo4j_client.execute_query(query, {
            "broker_id": broker_id,
            "depth": depth,
            "min_connections": min_connections
        })
        
        # Format the results
        network = []
        for result in results:
            broker_node = result["broker"]
            # Convert Neo4j node to dict
            broker_dict = dict(broker_node)
            # Convert datetime objects to strings if needed
            if "created_at" in broker_dict and broker_dict["created_at"]:
                broker_dict["created_at"] = str(broker_dict["created_at"])
            if "updated_at" in broker_dict and broker_dict["updated_at"]:
                broker_dict["updated_at"] = str(broker_dict["updated_at"])
            
            network.append({
                "broker": broker_dict,
                "connection_score": result["connection_score"],
                "common_properties": result["common_properties"],
                "total_properties": result["total_properties"]
            })
        
        return network
    finally:
        neo4j_client.close() 