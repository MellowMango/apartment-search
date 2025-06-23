"""
MongoDB client and database connection setup for Lynnapse.
"""

import os
import logging
from typing import Optional
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pymongo.errors import ConnectionFailure


logger = logging.getLogger(__name__)


class MongoDBClient:
    """MongoDB client wrapper for Lynnapse."""
    
    def __init__(self, connection_string: Optional[str] = None):
        """Initialize MongoDB client."""
        self.connection_string = connection_string or os.getenv(
            "MONGODB_URL", 
            "mongodb://localhost:27017"
        )
        self.database_name = os.getenv("MONGODB_DATABASE", "lynnapse")
        self.client: Optional[AsyncIOMotorClient] = None
        self.database: Optional[AsyncIOMotorDatabase] = None
    
    async def connect(self) -> None:
        """Connect to MongoDB."""
        try:
            self.client = AsyncIOMotorClient(self.connection_string)
            self.database = self.client[self.database_name]
            
            # Test the connection
            await self.client.admin.command('ping')
            logger.info(f"Connected to MongoDB database: {self.database_name}")
            
        except ConnectionFailure as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise
    
    async def disconnect(self) -> None:
        """Disconnect from MongoDB."""
        if self.client:
            self.client.close()
            logger.info("Disconnected from MongoDB")
    
    async def get_database(self) -> AsyncIOMotorDatabase:
        """Get the database instance."""
        if not self.database:
            await self.connect()
        return self.database
    
    async def create_indexes(self) -> None:
        """Create database indexes for better performance."""
        if not self.database:
            await self.connect()
        
        # Program indexes
        await self.database.programs.create_index([
            ("university_name", 1),
            ("program_name", 1)
        ], unique=True)
        await self.database.programs.create_index("program_url")
        await self.database.programs.create_index("scraped_at")
        
        # Faculty indexes
        await self.database.faculty.create_index([
            ("program_id", 1),
            ("name", 1)
        ])
        await self.database.faculty.create_index("email")
        await self.database.faculty.create_index("profile_url")
        await self.database.faculty.create_index("scraped_at")
        
        # Lab site indexes
        await self.database.lab_sites.create_index([
            ("faculty_id", 1),
            ("lab_url", 1)
        ], unique=True)
        await self.database.lab_sites.create_index("program_id")
        await self.database.lab_sites.create_index("scraped_at")
        
        # Scrape job indexes
        await self.database.scrape_jobs.create_index("job_name")
        await self.database.scrape_jobs.create_index("status")
        await self.database.scrape_jobs.create_index("created_at")
        await self.database.scrape_jobs.create_index("target_url")
        
        logger.info("Database indexes created successfully")
    
    async def health_check(self) -> bool:
        """Check if the database connection is healthy."""
        try:
            if not self.database:
                await self.connect()
            await self.client.admin.command('ping')
            return True
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return False


# Global client instance
_mongodb_client: Optional[MongoDBClient] = None


async def get_database() -> AsyncIOMotorDatabase:
    """Get the global database instance."""
    global _mongodb_client
    
    if not _mongodb_client:
        _mongodb_client = MongoDBClient()
        await _mongodb_client.connect()
    
    return await _mongodb_client.get_database()


async def get_client() -> MongoDBClient:
    """Get the global MongoDB client instance."""
    global _mongodb_client
    
    if not _mongodb_client:
        _mongodb_client = MongoDBClient()
        await _mongodb_client.connect()
    
    return _mongodb_client


async def close_database_connection() -> None:
    """Close the global database connection."""
    global _mongodb_client
    
    if _mongodb_client:
        await _mongodb_client.disconnect()
        _mongodb_client = None 