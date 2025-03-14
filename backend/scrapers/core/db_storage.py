#!/usr/bin/env python3
"""
Database storage module for saving scraped property data to Supabase and Neo4j.
"""

import os
import logging
import json
import uuid
from typing import Dict, Any, Optional, List

import httpx

logger = logging.getLogger(__name__)

class DatabaseStorage:
    """Database storage for scraper data."""
    
    def __init__(self):
        """Initialize the database storage with Supabase and Neo4j credentials."""
        # Get Supabase credentials from environment variables
        self.supabase_url = os.getenv("SUPABASE_URL")
        self.supabase_key = os.getenv("SUPABASE_KEY")
        
        if not self.supabase_url or not self.supabase_key:
            logger.warning("Missing Supabase credentials. Database storage will not work.")
        else:
            logger.info(f"Supabase URL: {self.supabase_url}")
            logger.info("Supabase key available")
        
        # Get Neo4j credentials from environment variables
        self.neo4j_uri = os.getenv("NEO4J_URI")
        self.neo4j_user = os.getenv("NEO4J_USER")
        self.neo4j_password = os.getenv("NEO4J_PASSWORD")
        
        if not all([self.neo4j_uri, self.neo4j_user, self.neo4j_password]):
            logger.warning("Missing Neo4j credentials. Graph database storage will not work.")
        else:
            logger.info(f"Neo4j URI: {self.neo4j_uri}")
            logger.info(f"Neo4j user: {self.neo4j_user}")
            logger.info("Neo4j password available")
    
    async def get_or_create_broker(self, broker_name: str, broker_url: str) -> str:
        """
        Get broker ID from database or create a new broker entry.
        
        Args:
            broker_name: Name of the broker
            broker_url: URL of the broker's website
            
        Returns:
            UUID of the broker as a string
        """
        if not all([self.supabase_url, self.supabase_key]):
            logger.error("Cannot get or create broker: Missing Supabase credentials")
            return str(uuid.uuid4())  # Return a random UUID as fallback
        
        try:
            # Create HTTP client
            async with httpx.AsyncClient() as client:
                # Check if broker exists
                headers = {
                    "apikey": self.supabase_key,
                    "Authorization": f"Bearer {self.supabase_key}",
                    "Content-Type": "application/json",
                    "Prefer": "return=representation"
                }
                
                # Query to find existing broker by name
                broker_name_encoded = broker_name.replace(" ", "%20")
                broker_query_url = f"{self.supabase_url}/rest/v1/brokers?name=eq.{broker_name_encoded}"
                
                logger.info(f"Checking if broker '{broker_name}' exists in database")
                response = await client.get(broker_query_url, headers=headers)
                
                if response.status_code == 200 and response.json():
                    # Broker exists, return its ID
                    broker_id = response.json()[0]["id"]
                    logger.info(f"Found existing broker with ID: {broker_id}")
                    return broker_id
                else:
                    # Create a new broker
                    logger.info(f"Broker '{broker_name}' not found. Creating new entry.")
                    new_broker = {
                        "name": broker_name,
                        "url": broker_url
                    }
                    
                    broker_create_url = f"{self.supabase_url}/rest/v1/brokers"
                    create_response = await client.post(
                        broker_create_url, 
                        headers=headers,
                        json=new_broker
                    )
                    
                    if create_response.status_code in (200, 201):
                        broker_id = create_response.json()[0]["id"]
                        logger.info(f"Created new broker with ID: {broker_id}")
                        return broker_id
                    else:
                        logger.error(f"Failed to create broker: {create_response.text}")
                        # Return a random UUID as fallback
                        return str(uuid.uuid4())
                        
        except Exception as e:
            logger.error(f"Error getting or creating broker: {str(e)}")
            # Return a random UUID as fallback
            return str(uuid.uuid4())
    
    async def save_property(self, property_data: Dict[str, Any]) -> bool:
        """
        Save a property to the database.
        
        Args:
            property_data: Dictionary containing property data
            
        Returns:
            True if successful, False otherwise
        """
        if not all([self.supabase_url, self.supabase_key]):
            logger.error("Cannot save property: Missing Supabase credentials")
            return False
        
        try:
            # Create HTTP client
            async with httpx.AsyncClient() as client:
                headers = {
                    "apikey": self.supabase_key,
                    "Authorization": f"Bearer {self.supabase_key}",
                    "Content-Type": "application/json",
                    "Prefer": "return=representation"
                }
                
                # Generate UUID if not provided
                if "id" not in property_data:
                    property_data["id"] = str(uuid.uuid4())
                    
                logger.info(f"Saving property with ID: {property_data['id']}")
                
                # Save to Supabase
                property_url = f"{self.supabase_url}/rest/v1/properties"
                response = await client.post(
                    property_url, 
                    headers=headers,
                    json=property_data
                )
                
                if response.status_code in (200, 201):
                    logger.info(f"Successfully saved property to Supabase")
                    return True
                else:
                    logger.error(f"Failed to save property to Supabase: {response.text}")
                    return False
                    
        except Exception as e:
            logger.error(f"Error saving property to database: {str(e)}")
            return False 