"""
Broker service for broker-related operations.

This module provides a service for broker operations using the repository pattern
for data access, maintaining backward compatibility with legacy code.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
import socketio
import logging

from app.core.config import settings
from app.schemas.broker import BrokerCreate, BrokerUpdate, Broker
from backend.app.models.broker_model import BrokerBase
from app.db.supabase import get_supabase_client
from app.db.neo4j_client import Neo4jClient
from backend.app.utils.architecture import layer, ArchitectureLayer, log_cross_layer_call
from backend.app.interfaces.api import DataProvider
from backend.app.interfaces.storage import PaginationParams, QueryResult
from backend.app.db.repository_factory import get_repository_factory
from backend.app.adapters.broker_adapter import BrokerAdapter
from backend.app.db.unit_of_work import get_unit_of_work

logger = logging.getLogger(__name__)


@layer(ArchitectureLayer.API)
class BrokerService(DataProvider):
    """Service for broker-related operations."""
    
    def __init__(self, repository_factory=None):
        """
        Initialize the broker service.
        
        Args:
            repository_factory: Factory for creating repositories
        """
        factory = repository_factory or get_repository_factory()
        self.broker_repository = factory.create_broker_repository()
        
        # For backward compatibility
        self.supabase = get_supabase_client()
        self.sio = socketio.AsyncClient()
        self.broker_adapter = BrokerAdapter()
    
    @log_cross_layer_call(ArchitectureLayer.API, ArchitectureLayer.STORAGE)
    async def get_brokers(
        self,
        skip: int = 0,
        limit: int = 100,
        company: Optional[str] = None
    ) -> List[Broker]:
        """
        Get brokers with optional filtering.
        
        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return
            company: Optional company filter
            
        Returns:
            List of brokers matching the criteria
        """
        # Set up filters and pagination
        filters = {}
        if company:
            filters["company"] = company
        
        pagination = PaginationParams(page=skip // limit + 1, page_size=limit)
        
        # Query brokers using repository
        query_result = await self.broker_repository.list(filters, pagination)
        
        # Convert to Broker objects for API
        brokers = [
            self.broker_adapter.to_schema(item, Broker)
            for item in query_result.items
        ]
        
        return brokers
    
    @log_cross_layer_call(ArchitectureLayer.API, ArchitectureLayer.STORAGE)
    async def get_broker(self, broker_id: str) -> Optional[Broker]:
        """
        Get a specific broker by ID.
        
        Args:
            broker_id: ID of the broker to retrieve
            
        Returns:
            Broker if found, None otherwise
        """
        broker = await self.broker_repository.get(broker_id)
        
        if not broker:
            return None
        
        # Convert to Broker schema for API
        return self.broker_adapter.to_schema(broker, Broker)
    
    @log_cross_layer_call(ArchitectureLayer.API, ArchitectureLayer.STORAGE)
    async def create_broker(self, broker_data: BrokerCreate) -> Broker:
        """
        Create a new broker.
        
        Args:
            broker_data: Broker data for creation
            
        Returns:
            Created broker
        """
        async with get_unit_of_work() as uow:
            # Convert from API schema to standardized model
            broker_dict = broker_data.dict()
            
            # Add timestamps
            now = datetime.utcnow()
            broker_dict.update({
                "created_at": now,
                "updated_at": now
            })
            
            # Convert to standardized model
            broker_model = self.broker_adapter.to_standardized_model(broker_dict)
            
            # Create broker using repository
            result = await uow.broker_repository.create(broker_model)
            
            if not result.success:
                raise ValueError(f"Failed to create broker: {result.error}")
            
            # Sync to Neo4j
            await self._sync_broker_to_neo4j(result.entity_id)
            
            # Notify clients about new broker
            if settings.ENABLE_REAL_TIME_UPDATES:
                broker_dict = self.broker_adapter.from_standardized_model(result.entity)
                await self.sio.emit("broker_created", broker_dict)
            
            await uow.commit()
            
            # Convert to Broker schema for API
            return self.broker_adapter.to_schema(result.entity, Broker)
    
    @log_cross_layer_call(ArchitectureLayer.API, ArchitectureLayer.STORAGE)
    async def update_broker(self, broker_id: str, broker_data: BrokerUpdate) -> Optional[Broker]:
        """
        Update a broker.
        
        Args:
            broker_id: ID of the broker to update
            broker_data: Broker data for update
            
        Returns:
            Updated broker if successful, None otherwise
        """
        async with get_unit_of_work() as uow:
            # Get current broker
            current_broker = await uow.broker_repository.get(broker_id)
            if not current_broker:
                return None
            
            # Update only provided fields
            broker_dict = broker_data.dict(exclude_unset=True)
            broker_dict["updated_at"] = datetime.utcnow()
            
            # Merge with current data
            for key, value in broker_dict.items():
                setattr(current_broker, key, value)
            
            # Update using repository
            result = await uow.broker_repository.update(broker_id, current_broker)
            
            if not result.success:
                logger.error(f"Failed to update broker: {result.error}")
                return None
            
            # Sync to Neo4j
            await self._sync_broker_to_neo4j(broker_id)
            
            # Notify clients about updated broker
            if settings.ENABLE_REAL_TIME_UPDATES:
                broker_dict = self.broker_adapter.from_standardized_model(result.entity)
                await self.sio.emit("broker_updated", broker_dict)
            
            await uow.commit()
            
            # Convert to Broker schema for API
            return self.broker_adapter.to_schema(result.entity, Broker)
    
    @log_cross_layer_call(ArchitectureLayer.API, ArchitectureLayer.STORAGE)
    async def delete_broker(self, broker_id: str) -> bool:
        """
        Delete a broker.
        
        Args:
            broker_id: ID of the broker to delete
            
        Returns:
            True if deletion was successful, False otherwise
        """
        async with get_unit_of_work() as uow:
            # Check if broker exists
            current_broker = await uow.broker_repository.get(broker_id)
            if not current_broker:
                return False
            
            # Delete using repository
            result = await uow.broker_repository.delete(broker_id)
            
            if not result.success:
                logger.error(f"Failed to delete broker: {result.error}")
                return False
            
            # Delete from Neo4j
            neo4j_client = Neo4jClient()
            try:
                neo4j_client.execute_query(
                    """
                    MATCH (b:Broker {id: $broker_id})
                    DETACH DELETE b
                    """,
                    {"broker_id": broker_id}
                )
            finally:
                neo4j_client.close()
            
            # Notify clients about deleted broker
            if settings.ENABLE_REAL_TIME_UPDATES:
                await self.sio.emit("broker_deleted", {"id": broker_id})
            
            await uow.commit()
            
            return True
    
    async def _sync_broker_to_neo4j(self, broker_id: str) -> None:
        """
        Sync a broker to Neo4j.
        
        Args:
            broker_id: ID of the broker to sync
        """
        # Get broker data
        broker_data = await self.broker_repository.get(broker_id)
        if not broker_data:
            return
        
        # Convert to dict
        broker_dict = self.broker_adapter.from_standardized_model(broker_data)
        
        # Convert datetime objects to strings
        if broker_dict.get("created_at"):
            broker_dict["created_at"] = broker_dict["created_at"].isoformat() \
                if not isinstance(broker_dict["created_at"], str) \
                else broker_dict["created_at"]
                
        if broker_dict.get("updated_at"):
            broker_dict["updated_at"] = broker_dict["updated_at"].isoformat() \
                if not isinstance(broker_dict["updated_at"], str) \
                else broker_dict["updated_at"]
        
        # Sync to Neo4j
        neo4j_client = Neo4jClient()
        try:
            # Check if broker exists in Neo4j
            result = neo4j_client.execute_query(
                """
                MATCH (b:Broker {id: $broker_id})
                RETURN COUNT(b) as count
                """,
                {"broker_id": broker_id}
            )
            
            broker_exists = result[0]["count"] > 0 if result else False
            
            if broker_exists:
                # Update broker
                neo4j_client.execute_query(
                    """
                    MATCH (b:Broker {id: $id})
                    SET b.name = $name,
                        b.company = $company,
                        b.email = $email,
                        b.phone = $phone,
                        b.website = $website,
                        b.updated_at = datetime($updated_at)
                    """,
                    broker_dict
                )
            else:
                # Create broker
                neo4j_client.create_broker(broker_dict)
        finally:
            neo4j_client.close()