from typing import List, Optional, Dict, Any
from datetime import datetime
import socketio

# Relative imports
from ..core.config import settings
from ..schemas.brokerage import BrokerageCreate, BrokerageUpdate, Brokerage
from ..db.supabase_client import get_supabase_client
from ..db.neo4j_client import Neo4jClient

class BrokerageService:
    def __init__(self):
        self.supabase = get_supabase_client()
        # Initialize sio only if needed
        if settings.ENABLE_REAL_TIME_UPDATES:
            self.sio = socketio.AsyncClient()
        else:
            self.sio = None
    
    async def get_brokerages(
        self,
        skip: int = 0,
        limit: int = 100,
        name: Optional[str] = None
    ) -> List[Brokerage]:
        """
        Get brokerages with optional filtering.
        """
        query = self.supabase.table("brokerages").select("*")
        
        # Apply filters
        if name:
            query = query.ilike("name", f"%{name}%")
        
        # Apply pagination
        query = query.range(skip, skip + limit - 1)
        
        # Execute query
        response = query.execute()
        
        # Convert to Brokerage objects
        brokerages = [Brokerage(**item) for item in response.data]
        
        return brokerages
    
    async def get_brokerage(self, brokerage_id: str) -> Optional[Brokerage]:
        """
        Get a specific brokerage by ID.
        """
        response = self.supabase.table("brokerages").select("*").eq("id", brokerage_id).execute()
        
        if not response.data:
            return None
        
        return Brokerage(**response.data[0])
    
    async def create_brokerage(self, brokerage_data: BrokerageCreate) -> Brokerage:
        """
        Create a new brokerage.
        """
        # Add timestamps
        now = datetime.utcnow()
        brokerage_dict = brokerage_data.dict()
        brokerage_dict.update({
            "created_at": now,
            "updated_at": now
        })
        
        # Insert into database
        response = self.supabase.table("brokerages").insert(brokerage_dict).execute()
        
        # Sync to Neo4j
        brokerage_id = response.data[0]["id"]
        await self._sync_brokerage_to_neo4j(brokerage_id)
        
        # Notify clients about new brokerage
        if self.sio and settings.ENABLE_REAL_TIME_UPDATES:
            await self.sio.emit("brokerage_created", response.data[0])
        
        return Brokerage(**response.data[0])
    
    async def update_brokerage(self, brokerage_id: str, brokerage_data: BrokerageUpdate) -> Optional[Brokerage]:
        """
        Update a brokerage.
        """
        # Get current brokerage
        current_brokerage = await self.get_brokerage(brokerage_id)
        if not current_brokerage:
            return None
        
        # Update timestamp
        brokerage_dict = brokerage_data.dict(exclude_unset=True)
        brokerage_dict["updated_at"] = datetime.utcnow()
        
        # Update in database
        response = self.supabase.table("brokerages").update(brokerage_dict).eq("id", brokerage_id).execute()
        
        if not response.data:
            return None
        
        # Sync to Neo4j
        await self._sync_brokerage_to_neo4j(brokerage_id)
        
        # Notify clients about updated brokerage
        if self.sio and settings.ENABLE_REAL_TIME_UPDATES:
            await self.sio.emit("brokerage_updated", response.data[0])
        
        return Brokerage(**response.data[0])
    
    async def delete_brokerage(self, brokerage_id: str) -> bool:
        """
        Delete a brokerage.
        """
        # Check if brokerage exists
        current_brokerage = await self.get_brokerage(brokerage_id)
        if not current_brokerage:
            return False
        
        # Delete from database
        response = self.supabase.table("brokerages").delete().eq("id", brokerage_id).execute()
        
        # Delete from Neo4j
        neo4j_client = Neo4jClient()
        try:
            neo4j_client.execute_query(
                """
                MATCH (b:Brokerage {id: $brokerage_id})
                DETACH DELETE b
                """,
                {"brokerage_id": brokerage_id}
            )
        finally:
            neo4j_client.close()
        
        # Notify clients about deleted brokerage
        if self.sio and settings.ENABLE_REAL_TIME_UPDATES:
            await self.sio.emit("brokerage_deleted", {"id": brokerage_id})
        
        return True
    
    async def _sync_brokerage_to_neo4j(self, brokerage_id: str) -> None:
        """
        Sync a brokerage to Neo4j.
        """
        # Get brokerage data
        brokerage_data = await self.get_brokerage(brokerage_id)
        if not brokerage_data:
            return
        
        # Convert to dict
        brokerage_dict = brokerage_data.dict()
        
        # Convert datetime objects to strings
        if brokerage_dict.get("created_at"):
            brokerage_dict["created_at"] = brokerage_dict["created_at"].isoformat()
        if brokerage_dict.get("updated_at"):
            brokerage_dict["updated_at"] = brokerage_dict["updated_at"].isoformat()
        
        # Sync to Neo4j
        neo4j_client = Neo4jClient()
        try:
            # Check if brokerage exists in Neo4j
            result = neo4j_client.execute_query(
                """
                MATCH (b:Brokerage {id: $brokerage_id})
                RETURN COUNT(b) as count
                """,
                {"brokerage_id": brokerage_id}
            )
            
            brokerage_exists = result[0]["count"] > 0 if result else False
            
            if brokerage_exists:
                # Update brokerage
                neo4j_client.execute_query(
                    """
                    MATCH (b:Brokerage {id: $id})
                    SET b.name = $name,
                        b.website = $website,
                        b.logo_url = $logo_url,
                        b.address = $address,
                        b.city = $city,
                        b.state = $state,
                        b.zip_code = $zip_code,
                        b.updated_at = datetime($updated_at)
                    """,
                    brokerage_dict
                )
            else:
                # Create brokerage
                neo4j_client.execute_query(
                    """
                    CREATE (b:Brokerage {
                        id: $id,
                        name: $name,
                        website: $website,
                        logo_url: $logo_url,
                        address: $address,
                        city: $city,
                        state: $state,
                        zip_code: $zip_code,
                        created_at: datetime($created_at),
                        updated_at: datetime($updated_at)
                    })
                    """,
                    brokerage_dict
                )
        finally:
            neo4j_client.close() 