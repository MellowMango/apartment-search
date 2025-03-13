from typing import List, Optional, Dict, Any
from datetime import datetime
import socketio

from app.core.config import settings
from app.schemas.broker import BrokerCreate, BrokerUpdate, Broker
from app.db.supabase import get_supabase_client
from app.db.neo4j_client import Neo4jClient

class BrokerService:
    def __init__(self):
        self.supabase = get_supabase_client()
        self.sio = socketio.AsyncClient()
    
    async def get_brokers(
        self,
        skip: int = 0,
        limit: int = 100,
        company: Optional[str] = None
    ) -> List[Broker]:
        """
        Get brokers with optional filtering.
        """
        query = self.supabase.table("brokers").select("*")
        
        # Apply filters
        if company:
            query = query.eq("company", company)
        
        # Apply pagination
        query = query.range(skip, skip + limit - 1)
        
        # Execute query
        response = query.execute()
        
        # Convert to Broker objects
        brokers = [Broker(**item) for item in response.data]
        
        return brokers
    
    async def get_broker(self, broker_id: str) -> Optional[Broker]:
        """
        Get a specific broker by ID.
        """
        response = self.supabase.table("brokers").select("*").eq("id", broker_id).execute()
        
        if not response.data:
            return None
        
        return Broker(**response.data[0])
    
    async def create_broker(self, broker_data: BrokerCreate) -> Broker:
        """
        Create a new broker.
        """
        # Add timestamps
        now = datetime.utcnow()
        broker_dict = broker_data.dict()
        broker_dict.update({
            "created_at": now,
            "updated_at": now
        })
        
        # Insert into database
        response = self.supabase.table("brokers").insert(broker_dict).execute()
        
        # Sync to Neo4j
        broker_id = response.data[0]["id"]
        await self._sync_broker_to_neo4j(broker_id)
        
        # Notify clients about new broker
        if settings.ENABLE_REAL_TIME_UPDATES:
            await self.sio.emit("broker_created", response.data[0])
        
        return Broker(**response.data[0])
    
    async def update_broker(self, broker_id: str, broker_data: BrokerUpdate) -> Optional[Broker]:
        """
        Update a broker.
        """
        # Get current broker
        current_broker = await self.get_broker(broker_id)
        if not current_broker:
            return None
        
        # Update timestamp
        broker_dict = broker_data.dict(exclude_unset=True)
        broker_dict["updated_at"] = datetime.utcnow()
        
        # Update in database
        response = self.supabase.table("brokers").update(broker_dict).eq("id", broker_id).execute()
        
        if not response.data:
            return None
        
        # Sync to Neo4j
        await self._sync_broker_to_neo4j(broker_id)
        
        # Notify clients about updated broker
        if settings.ENABLE_REAL_TIME_UPDATES:
            await self.sio.emit("broker_updated", response.data[0])
        
        return Broker(**response.data[0])
    
    async def delete_broker(self, broker_id: str) -> bool:
        """
        Delete a broker.
        """
        # Check if broker exists
        current_broker = await self.get_broker(broker_id)
        if not current_broker:
            return False
        
        # Delete from database
        response = self.supabase.table("brokers").delete().eq("id", broker_id).execute()
        
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
        
        return True
    
    async def _sync_broker_to_neo4j(self, broker_id: str) -> None:
        """
        Sync a broker to Neo4j.
        """
        # Get broker data
        broker_data = await self.get_broker(broker_id)
        if not broker_data:
            return
        
        # Convert to dict
        broker_dict = broker_data.dict()
        
        # Convert datetime objects to strings
        if broker_dict.get("created_at"):
            broker_dict["created_at"] = broker_dict["created_at"].isoformat()
        if broker_dict.get("updated_at"):
            broker_dict["updated_at"] = broker_dict["updated_at"].isoformat()
        
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