"""
Storage utilities for saving scraper results to files and databases.
"""

import os
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Union

logger = logging.getLogger(__name__)

class DataStorage:
    """
    Utility for storing extracted data from web scrapers.
    """
    
    def __init__(self, source_name: str, base_data_dir: str = "data"):
        """
        Initialize the data storage.
        
        Args:
            source_name: The name of the data source (e.g., "acrmultifamily").
            base_data_dir: The base directory for storing data.
        """
        self.source_name = source_name
        self.base_data_dir = Path(base_data_dir)
        
        # Ensure directories exist
        self.screenshots_dir = self.base_data_dir / "screenshots" / source_name
        self.html_dir = self.base_data_dir / "html" / source_name
        self.extracted_dir = self.base_data_dir / "extracted" / source_name
        
        os.makedirs(self.screenshots_dir, exist_ok=True)
        os.makedirs(self.html_dir, exist_ok=True)
        os.makedirs(self.extracted_dir, exist_ok=True)
    
    def save_screenshot(self, screenshot_data: str, timestamp: Optional[datetime] = None) -> str:
        """
        Save a screenshot to a file.
        
        Args:
            screenshot_data: The base64-encoded screenshot data.
            timestamp: The timestamp to use for the filename. Defaults to current time.
            
        Returns:
            The path to the saved screenshot file.
        """
        if not timestamp:
            timestamp = datetime.now()
            
        timestamp_str = timestamp.strftime("%Y%m%d-%H%M%S")
        filename = f"{timestamp_str}.txt"
        filepath = self.screenshots_dir / filename
        
        with open(filepath, "w") as f:
            f.write(screenshot_data)
            
        logger.info(f"Screenshot saved to {filepath}")
        return str(filepath)
    
    def save_html(self, html_content: str, timestamp: Optional[datetime] = None) -> str:
        """
        Save HTML content to a file.
        
        Args:
            html_content: The HTML content to save.
            timestamp: The timestamp to use for the filename. Defaults to current time.
            
        Returns:
            The path to the saved HTML file.
        """
        if not timestamp:
            timestamp = datetime.now()
            
        timestamp_str = timestamp.strftime("%Y%m%d-%H%M%S")
        filename = f"{timestamp_str}.html"
        filepath = self.html_dir / filename
        
        with open(filepath, "w") as f:
            f.write(html_content)
            
        logger.info(f"HTML content saved to {filepath}")
        
        # Also save a preview for easier viewing
        preview_length = min(10000, len(html_content))
        preview_filename = f"preview-{timestamp_str}.txt"
        preview_filepath = self.html_dir / preview_filename
        
        with open(preview_filepath, "w") as f:
            f.write(html_content[:preview_length])
            
        logger.info(f"HTML preview saved to {preview_filepath}")
        return str(filepath)
    
    def save_extracted_data(self, data: Union[Dict[str, Any], List[Dict[str, Any]]], 
                          data_type: str = "properties",
                          timestamp: Optional[datetime] = None) -> str:
        """
        Save extracted data to a JSON file.
        
        Args:
            data: The data to save.
            data_type: The type of data (e.g., "properties").
            timestamp: The timestamp to use for the filename. Defaults to current time.
            
        Returns:
            The path to the saved JSON file.
        """
        if not timestamp:
            timestamp = datetime.now()
            
        timestamp_str = timestamp.strftime("%Y%m%d-%H%M%S")
        filename = f"{data_type}-{timestamp_str}.json"
        filepath = self.extracted_dir / filename
        
        with open(filepath, "w") as f:
            json.dump(data, f, indent=2)
            
        logger.info(f"Extracted data saved to {filepath}")
        return str(filepath)
    
    async def save_to_database(self, data: Union[Dict[str, Any], List[Dict[str, Any]]],
                            data_type: str = "properties") -> bool:
        """
        Save extracted data to both Supabase and Neo4j databases.
        
        Args:
            data: The data to save. Can be a single property dict or a list of property dicts.
            data_type: The type of data (e.g., "properties").
            
        Returns:
            True if successful, False otherwise.
        """
        try:
            import os
            import uuid
            from datetime import datetime
            from dotenv import load_dotenv
            import sys
            
            # Force load backend .env file to ensure we use the correct credentials
            backend_env_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../.env"))
            logger.info(f"Force loading environment variables from: {backend_env_path}")
            if os.path.exists(backend_env_path):
                load_dotenv(backend_env_path, override=True)
                logger.info("Backend .env loaded successfully")
            else:
                logger.warning(f"Backend .env file not found at: {backend_env_path}")
            
            # Import database clients
            try:
                from backend.app.db.supabase_client import get_supabase_client
                from backend.app.db.neo4j_client import Neo4jClient
            except ImportError:
                # Fallback to relative imports for different project structures
                sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../")))
                from app.db.supabase_client import get_supabase_client
                from app.db.neo4j_client import Neo4jClient
            
            # Log the Supabase URL being used (but not sensitive keys)
            logger.info(f"Using Supabase URL: {os.getenv('SUPABASE_URL')}")
            logger.info(f"Using Neo4j URI: {os.getenv('NEO4J_URI')}")
            
            # Check if we're dealing with a list or single item
            if isinstance(data, dict) and data_type == "properties":
                properties_data = data.get("properties", [])
            elif isinstance(data, list):
                properties_data = data
            else:
                properties_data = []
            
            if not properties_data:
                logger.warning(f"No properties found in data to save to database")
                return False
            
            # Get database clients
            try:
                supabase_client = get_supabase_client()
                neo4j_client = Neo4jClient()
                logger.info("Successfully connected to databases")
            except Exception as e:
                logger.error(f"Failed to connect to databases: {str(e)}")
                return False
            
            successful_saves = 0
            
            # Process each property
            for property_item in properties_data:
                try:
                    # Generate a UUID for the property
                    property_id = str(uuid.uuid4())
                    
                    # Extract property data
                    property_data = {
                        "id": property_id,
                        "name": property_item.get("title", ""),
                        "address": property_item.get("location", ""),
                        "city": "Unknown",
                        "state": "TX",  # Default
                        "zip_code": "",
                        "price": 0,  # Default
                        "units": int(property_item.get("units", 0)) if property_item.get("units", "").isdigit() else 0,
                        "year_built": int(property_item.get("year_built", 0)) if property_item.get("year_built", "").isdigit() else 0,
                        "square_feet": 0,  # Default
                        "property_type": "multifamily",  # Default for ACR Multifamily
                        "property_status": property_item.get("status", "active"),
                        "property_website": property_item.get("link", ""),
                        "source_website": self.source_name,  # Use source_website instead of listing_website
                        "description": property_item.get("description", ""),
                        "created_at": datetime.now().isoformat(),
                        "updated_at": datetime.now().isoformat(),
                    }
                    
                    # Extract city and state from location if available
                    if property_item.get("location"):
                        location_parts = property_item.get("location", "").split(",")
                        if len(location_parts) >= 2:
                            property_data["city"] = location_parts[0].strip()
                            property_data["state"] = location_parts[1].strip()
                    
                    # Insert property into Supabase
                    logger.info(f"Inserting property {property_data['name']} into Supabase")
                    
                    # Remove fields that don't exist in the Supabase schema
                    # This is a temporary fix until we update the schema
                    if "listing_website" in property_data:
                        del property_data["listing_website"]
                    if "property_website" in property_data:
                        del property_data["property_website"]
                    if "source_website" in property_data:
                        del property_data["source_website"]
                    
                    supabase_result = supabase_client.table("properties").insert(property_data).execute()
                    
                    if not supabase_result.data:
                        logger.error(f"Failed to insert property {property_data['name']} into Supabase")
                        continue
                        
                    logger.info(f"Successfully inserted property {property_data['name']} into Supabase")
                    
                    # Insert property into Neo4j
                    logger.info(f"Inserting property {property_data['name']} into Neo4j")
                    neo4j_result = neo4j_client.create_property(property_data)
                    
                    if not neo4j_result:
                        logger.error(f"Failed to insert property {property_data['name']} into Neo4j")
                        continue
                        
                    logger.info(f"Successfully inserted property {property_data['name']} into Neo4j")
                    successful_saves += 1
                    
                except Exception as e:
                    logger.error(f"Error saving property to database: {str(e)}")
                    continue
                
            # Close Neo4j client
            neo4j_client.close()
            
            success_rate = successful_saves / len(properties_data) if properties_data else 0
            logger.info(f"Saved {successful_saves}/{len(properties_data)} properties to database (success rate: {success_rate:.2%})")
            
            # Consider it successful if at least one property was saved
            return successful_saves > 0
            
        except Exception as e:
            logger.error(f"Error saving data to database: {str(e)}")
            return False 