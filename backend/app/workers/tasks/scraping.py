import logging
from typing import List, Dict, Any
import requests
from bs4 import BeautifulSoup
from datetime import datetime

# Relative imports
from ..celery_app import celery_app
from ...db.supabase_client import get_supabase_client
from ...core.config import settings

logger = logging.getLogger(__name__)

@celery_app.task
def scrape_broker_websites():
    """
    Scrape broker websites for property listings.
    """
    logger.info("Starting broker website scraping")
    
    # Get list of broker websites to scrape
    supabase = get_supabase_client()
    response = supabase.table("broker_websites").select("*").execute()
    
    if not response.data:
        logger.info("No broker websites found to scrape")
        return
    
    # Scrape each website
    for website in response.data:
        try:
            scrape_broker_website.delay(website)
        except Exception as e:
            logger.error(f"Error scheduling scrape for {website['url']}: {str(e)}")
    
    logger.info(f"Scheduled scraping for {len(response.data)} broker websites")

@celery_app.task
def scrape_broker_website(website: Dict[str, Any]):
    """
    Scrape a single broker website for property listings.
    """
    logger.info(f"Scraping broker website: {website['url']}")
    
    try:
        # Make request to website
        headers = {
            "User-Agent": settings.SCRAPER_USER_AGENT
        }
        response = requests.get(
            website["url"],
            headers=headers,
            timeout=settings.SCRAPER_TIMEOUT
        )
        response.raise_for_status()
        
        # Parse HTML
        soup = BeautifulSoup(response.text, "html.parser")
        
        # Extract property listings (this is a placeholder - actual implementation will depend on website structure)
        properties = extract_properties(soup, website)
        
        # Save properties to database
        save_properties(properties, website["brokerage_id"])
        
        logger.info(f"Successfully scraped {len(properties)} properties from {website['url']}")
        
        # Update last scraped timestamp
        supabase = get_supabase_client()
        supabase.table("broker_websites").update({
            "last_scraped": datetime.utcnow().isoformat()
        }).eq("id", website["id"]).execute()
        
    except Exception as e:
        logger.error(f"Error scraping {website['url']}: {str(e)}")
        # Record the error
        supabase = get_supabase_client()
        supabase.table("scraping_errors").insert({
            "broker_website_id": website["id"],
            "error_message": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }).execute()

def extract_properties(soup: BeautifulSoup, website: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Extract property listings from HTML.
    This is a placeholder - actual implementation will depend on website structure.
    """
    properties = []
    
    # Example implementation - will need to be customized for each broker website
    property_elements = soup.select(website.get("property_selector", ".property-listing"))
    
    for element in property_elements:
        try:
            property_data = {
                "name": extract_text(element, website.get("name_selector", ".property-name")),
                "address": extract_text(element, website.get("address_selector", ".property-address")),
                "num_units": extract_number(element, website.get("units_selector", ".property-units")),
                "year_built": extract_number(element, website.get("year_built_selector", ".property-year")),
                "brokerage_id": website["brokerage_id"],
                "listing_website": extract_link(element, website.get("listing_link_selector", "a")),
                "status": "Actively Marketed"  # Default status
            }
            
            # Only add if we have the minimum required data
            if property_data["name"] and property_data["address"] and property_data["num_units"]:
                properties.append(property_data)
                
        except Exception as e:
            logger.error(f"Error extracting property data: {str(e)}")
    
    return properties

def extract_text(element: BeautifulSoup, selector: str) -> str:
    """Extract text from an element using a CSS selector."""
    selected = element.select_one(selector)
    return selected.get_text().strip() if selected else ""

def extract_number(element: BeautifulSoup, selector: str) -> int:
    """Extract a number from an element using a CSS selector."""
    text = extract_text(element, selector)
    # Extract digits only
    digits = ''.join(c for c in text if c.isdigit())
    return int(digits) if digits else 0

def extract_link(element: BeautifulSoup, selector: str) -> str:
    """Extract a link from an element using a CSS selector."""
    selected = element.select_one(selector)
    return selected.get('href', '') if selected else ""

def save_properties(properties: List[Dict[str, Any]], brokerage_id: str):
    """
    Save properties to the database.
    """
    if not properties:
        return
    
    supabase = get_supabase_client()
    
    for property_data in properties:
        try:
            # Check if property already exists (by address)
            response = supabase.table("properties").select("*").eq("address", property_data["address"]).execute()
            
            if response.data:
                # Property exists, update it
                property_id = response.data[0]["id"]
                property_data["date_updated"] = datetime.utcnow().isoformat()
                supabase.table("properties").update(property_data).eq("id", property_id).execute()
            else:
                # New property, insert it
                now = datetime.utcnow().isoformat()
                property_data.update({
                    "date_first_appeared": now,
                    "date_updated": now
                })
                supabase.table("properties").insert(property_data).execute()
                
        except Exception as e:
            logger.error(f"Error saving property {property_data.get('name', 'unknown')}: {str(e)}") 