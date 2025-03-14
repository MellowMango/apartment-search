#!/usr/bin/env python3
"""
Storage module for scrapers.
Handles saving data to files and databases.
"""

import os
import json
import logging
import datetime
import base64
from pathlib import Path
from typing import List, Dict, Any, Optional, Union

logger = logging.getLogger(__name__)

class ScraperDataStorage:
    """Storage class for scraper data."""
    
    def __init__(self, broker_name: str, save_to_db: bool = False):
        """
        Initialize the storage with the broker name.
        
        Args:
            broker_name: Name of the broker website being scraped
            save_to_db: Whether to save data to database
        """
        self.broker_name = broker_name.lower().replace(' ', '')
        self.save_to_db = save_to_db
        
        # Create data directories if they don't exist
        self.data_dir = Path("data")
        self.screenshots_dir = self.data_dir / "screenshots" / self.broker_name
        self.html_dir = self.data_dir / "html" / self.broker_name
        self.extracted_dir = self.data_dir / "extracted" / self.broker_name
        
        self.screenshots_dir.mkdir(parents=True, exist_ok=True)
        self.html_dir.mkdir(parents=True, exist_ok=True)
        self.extracted_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Initialized storage for {broker_name}")
    
    async def save_screenshot(self, screenshot_data: str) -> str:
        """
        Save a screenshot to the screenshots directory.
        
        Args:
            screenshot_data: Base64-encoded screenshot data
            
        Returns:
            Path to the saved screenshot file
        """
        if not screenshot_data:
            logger.warning("No screenshot data to save")
            return ""
            
        timestamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
        filename = f"{timestamp}.txt"
        filepath = self.screenshots_dir / filename
        
        with open(filepath, "w") as f:
            f.write(screenshot_data)
            
        logger.info(f"Screenshot saved to {filepath}")
        return str(filepath)
    
    async def save_html_content(self, html_content: str) -> str:
        """
        Save HTML content to the html directory.
        
        Args:
            html_content: HTML content to save
            
        Returns:
            Path to the saved HTML file
        """
        if not html_content:
            logger.warning("No HTML content to save")
            return ""
        
        timestamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
        html_filename = f"{timestamp}.html"
        preview_filename = f"preview-{timestamp}.txt"
        
        html_filepath = self.html_dir / html_filename
        preview_filepath = self.html_dir / preview_filename
        
        # Save the full HTML
        with open(html_filepath, "w", encoding="utf-8") as f:
            f.write(html_content)
        
        # Save a preview (first 500 chars)
        with open(preview_filepath, "w", encoding="utf-8") as f:
            f.write(html_content[:500] + "..." if len(html_content) > 500 else html_content)
        
        logger.info(f"HTML content saved to {html_filepath}")
        logger.info(f"HTML preview saved to {preview_filepath}")
        return str(html_filepath)
    
    async def save_extracted_data(self, extracted_data: List[Dict[str, Any]]) -> str:
        """
        Save extracted data to the extracted directory.
        
        Args:
            extracted_data: List of property dictionaries to save
            
        Returns:
            Path to the saved JSON file
        """
        if not extracted_data:
            logger.warning("No extracted data to save")
            return ""
            
        timestamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
        filename = f"properties-{timestamp}.json"
        filepath = self.extracted_dir / filename
        
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(extracted_data, f, indent=2)
            
        logger.info(f"Extracted data saved to {filepath}")
        return str(filepath)
    
    async def save_to_database(self, properties: List[Dict[str, Any]]) -> bool:
        """
        Save property data to both Supabase and Neo4j databases.
        
        Args:
            properties: List of property dictionaries to save to database
            
        Returns:
            True if all properties were saved successfully, False otherwise
        """
        if not self.save_to_db:
            logger.info("Database saving disabled, skipping")
            return False
        
        if not properties:
            logger.warning("No properties to save to database")
            return False
        
        try:
            # Force load environment variables - simplified path handling
            from dotenv import load_dotenv
            
            # Try multiple potential .env locations
            env_files = [
                os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), ".env"),
                os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))), ".env"),
                os.path.join(os.getcwd(), ".env"),
                os.path.join(os.getcwd(), "backend", ".env")
            ]
            
            env_loaded = False
            for env_file in env_files:
                if os.path.exists(env_file):
                    logger.info(f"Loading environment variables from: {env_file}")
                    load_dotenv(dotenv_path=env_file, override=True)
                    env_loaded = True
                    break
            
            if not env_loaded:
                logger.warning("Could not find .env file, using existing environment variables")
            
            # Get database credentials from environment variables
            supabase_url = os.environ.get("SUPABASE_URL")
            supabase_key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")  # Use service role key to bypass RLS
            
            # Log available credentials (without revealing sensitive info)
            logger.info(f"Supabase URL: {supabase_url}")
            
            # Verify minimum required credentials for Supabase
            if not supabase_url or not supabase_key:
                logger.error("Missing Supabase credentials in environment variables")
                return False
            
            # Import database modules
            try:
                import pandas as pd
                from supabase import create_client, Client
                
                # Initialize Supabase client
                supabase: Client = create_client(supabase_url, supabase_key)
                
                # Initialize Neo4j if credentials are provided
                neo4j_uri = os.environ.get("NEO4J_URI")
                neo4j_user = os.environ.get("NEO4J_USERNAME")
                neo4j_password = os.environ.get("NEO4J_PASSWORD")
                
                # Create a flag to check if Neo4j is available
                neo4j_available = all([neo4j_uri, neo4j_user, neo4j_password])
                
                if neo4j_available:
                    try:
                        from neo4j import GraphDatabase
                        logger.info(f"Neo4j URI: {neo4j_uri}")
                        logger.info("Neo4j credentials available")
                    except ImportError:
                        neo4j_available = False
                        logger.warning("Neo4j Python driver not installed, skipping Neo4j integration")
                
                # Process properties
                success_count = 0
                
                # First, get or create broker entry
                try:
                    broker_name = self.broker_name.title()  # Proper case for display
                    website_url = ""
                    
                    # Use the first property's source_url if available, or construct a default URL
                    if properties and 'source_url' in properties[0]:
                        website_url = properties[0]['source_url']
                    elif properties and 'link' in properties[0]:
                        website_url = properties[0]['link']
                    else:
                        # Construct a default URL based on broker name
                        website_url = f"https://{self.broker_name.lower()}.com"
                    
                    broker_data = {
                        "name": broker_name,
                        "website": website_url,
                        "created_at": datetime.datetime.now().isoformat(),
                        "updated_at": datetime.datetime.now().isoformat()
                    }
                    
                    # Try to find the broker by name
                    logger.info(f"Checking if broker {broker_name} exists in database")
                    broker_resp = supabase.table("brokers").select("*").eq("name", broker_name).execute()
                    broker_exists = broker_resp.data and len(broker_resp.data) > 0
                    
                    if not broker_exists:
                        logger.info(f"Adding broker {broker_name} to database")
                        broker_result = supabase.table("brokers").insert(broker_data).execute()
                        broker_id = broker_result.data[0]["id"] if broker_result.data else None
                        logger.info(f"Created broker with ID: {broker_id}")
                    else:
                        logger.info(f"Broker {broker_name} already exists in database")
                        broker_id = broker_resp.data[0]["id"]
                        logger.info(f"Using existing broker with ID: {broker_id}")
                        
                        # Update broker timestamp
                        logger.info(f"Updating broker {broker_name} timestamp")
                        supabase.table("brokers").update({"updated_at": datetime.datetime.now().isoformat()}).eq("id", broker_id).execute()
                        
                except Exception as e:
                    logger.warning(f"Error handling broker data: {e}")
                    broker_id = None
                
                # Transform property data to match expected schema
                for prop in properties:
                    try:
                        # Transform the property data to match the expected schema
                        db_property = {
                            "name": prop.get("title", "Unknown Property"),
                            "description": prop.get("description", ""),
                            "address": prop.get("location", ""),
                            "city": "",  # Extract from location if possible
                            "state": "",  # Extract from location if possible
                            "zip_code": "",  # Extract from location if possible
                            "units": prop.get("units", 0),
                            "year_built": prop.get("year_built", 0),
                            "price": prop.get("price", 0),
                            "property_status": prop.get("status", "Available"),
                            "property_type": "Multifamily",  # Default property type
                            "amenities": [],  # Empty array for amenities
                            "images": [],  # Empty array for images
                            "created_at": datetime.datetime.now().isoformat(),
                            "updated_at": datetime.datetime.now().isoformat()
                        }
                        
                        # Set default values for required numeric fields
                        db_property.setdefault("latitude", 0.0)
                        db_property.setdefault("longitude", 0.0)
                        db_property.setdefault("price_per_unit", 0)
                        db_property.setdefault("price_per_sqft", 0)
                        db_property.setdefault("cap_rate", 0.0)
                        db_property.setdefault("square_feet", 0)
                        
                        # Add broker_id to link properties to brokers
                        if broker_id:
                            db_property["broker_id"] = broker_id
                        
                        # Try to parse location into city, state, zip if present
                        if prop.get("location"):
                            location = prop.get("location", "")
                            
                            # Simple regex patterns to extract city, state, zip from location
                            import re
                            
                            # Try to extract state (2 letter code)
                            state_match = re.search(r'\b([A-Z]{2})\b', location)
                            if state_match:
                                db_property["state"] = state_match.group(1)
                            
                            # Try to extract zip code (5 digits)
                            zip_match = re.search(r'\b(\d{5})\b', location)
                            if zip_match:
                                db_property["zip_code"] = zip_match.group(1)
                            
                            # Try to extract city (anything before state)
                            if state_match:
                                city_match = re.search(r'([^,]+),\s*' + state_match.group(1), location)
                                if city_match:
                                    db_property["city"] = city_match.group(1).strip()
                        
                        # Convert numeric fields to proper format
                        for field in ["units", "year_built", "price", "square_feet", "price_per_unit", "price_per_sqft"]:
                            try:
                                if db_property[field] and str(db_property[field]).strip():
                                    # Remove non-numeric characters and convert to integer
                                    value = ''.join(c for c in str(db_property[field]) if c.isdigit() or c == '.')
                                    if value:
                                        if field in ["price", "price_per_unit", "price_per_sqft", "cap_rate"]:
                                            db_property[field] = float(value)
                                        else:
                                            db_property[field] = int(value)
                                    else:
                                        db_property[field] = 0
                                else:
                                    db_property[field] = 0
                            except Exception as e:
                                logger.warning(f"Error converting {field}: {e}")
                                db_property[field] = 0
                        
                        # Insert into Supabase
                        logger.info(f"Inserting property {db_property['name']} into Supabase")
                        result = supabase.table("properties").insert(db_property).execute()
                        logger.info(f"Successfully inserted property {db_property['name']} into Supabase (ID: {result.data[0]['id'] if result.data else None})")
                        
                        success_count += 1
                    except Exception as e:
                        logger.error(f"Error saving property to database: {e}")
                
                # Calculate success rate
                success_rate = (success_count / len(properties)) * 100 if properties else 0
                logger.info(f"Saved {success_count}/{len(properties)} properties to database (success rate: {success_rate:.2f}%)")
                
                # Consider partial success as success for now
                return success_count > 0
            
            except ImportError as e:
                logger.error(f"Missing required database libraries: {e}")
                return False
                
        except Exception as e:
            logger.error(f"Error saving to database: {e}")
        return False 
    
    def _create_property_node(self, tx, property_data):
        """
        Create a property node in Neo4j.
        
        Args:
            tx: Neo4j transaction
            property_data: Property data dictionary
        """
        query = """
        MERGE (p:Property {
            title: $title,
            broker_name: $broker_name,
            source_website: $source_website
        })
        SET p.location = $location,
            p.units = $units,
            p.year_built = $year_built,
            p.status = $status,
            p.link = $link,
            p.description = $description,
            p.price = $price,
            p.source_url = $source_url,
            p.latitude = $latitude,
            p.longitude = $longitude,
            p.price_per_unit = $price_per_unit,
            p.price_per_sqft = $price_per_sqft,
            p.cap_rate = $cap_rate,
            p.last_updated = datetime()
        """
        
        # Set default values for any missing fields
        params = {
            "title": property_data.get("title", "Unknown Property"),
            "broker_name": property_data.get("broker_name", "Unknown Broker"),
            "source_website": property_data.get("source_website", self.broker_name),
            "location": property_data.get("location", ""),
            "units": property_data.get("units", ""),
            "year_built": property_data.get("year_built", ""),
            "status": property_data.get("status", "Available"),
            "link": property_data.get("link", ""),
            "description": property_data.get("description", ""),
            "price": property_data.get("price", ""),
            "source_url": property_data.get("source_url", ""),
            "latitude": property_data.get("latitude", 0.0),
            "longitude": property_data.get("longitude", 0.0),
            "price_per_unit": property_data.get("price_per_unit", 0),
            "price_per_sqft": property_data.get("price_per_sqft", 0),
            "cap_rate": property_data.get("cap_rate", 0.0)
        }
        
        return tx.run(query, **params) 