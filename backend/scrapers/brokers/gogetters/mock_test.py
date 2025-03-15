#!/usr/bin/env python
"""
Mock test script for GoGetters Multifamily scraper.
This script tests the scraper's parsing logic without requiring the MCP server.
"""

import asyncio
import sys
import os
import json
from datetime import datetime
import logging
from typing import Dict, Any, List, Optional

# Set up logging
logging.basicConfig(level=logging.INFO, 
                  format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Sample HTML content for testing
SAMPLE_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>GoGetters Multifamily - Current Listings</title>
</head>
<body>
    <div class="listings-container">
        <div class="property-card">
            <h3 class="title">Oakwood Apartments</h3>
            <div class="location">Dallas, TX</div>
            <div class="description">Great investment opportunity with 120 units in a prime location.</div>
            <div class="details">
                <span class="price">$25,000,000</span>
                <span class="units">120 units</span>
                <span class="sq-ft">150,000 sq ft</span>
                <span class="status">Available</span>
            </div>
            <a href="https://www.gogettersmultifamily.com/property/oakwood">View Details</a>
            <img src="https://www.gogettersmultifamily.com/images/oakwood.jpg" alt="Oakwood Apartments">
        </div>
        
        <div class="property-card">
            <h3 class="title">Pinecrest Multifamily</h3>
            <div class="location">Houston, TX</div>
            <div class="description">Value-add opportunity with 80 units in growing submarket.</div>
            <div class="details">
                <span class="price">$18,500,000</span>
                <span class="units">80 units</span>
                <span class="sq-ft">100,000 sq ft</span>
                <span class="status">Available</span>
            </div>
            <a href="https://www.gogettersmultifamily.com/property/pinecrest">View Details</a>
            <img src="https://www.gogettersmultifamily.com/images/pinecrest.jpg" alt="Pinecrest Multifamily">
        </div>
        
        <div class="property-card">
            <h3 class="title">Riverside Apartments</h3>
            <div class="location">Austin, TX</div>
            <div class="description">Newly renovated apartment complex with 60 units.</div>
            <div class="details">
                <span class="price">$15,000,000</span>
                <span class="units">60 units</span>
                <span class="sq-ft">75,000 sq ft</span>
                <span class="status">Under Contract</span>
            </div>
            <a href="https://www.gogettersmultifamily.com/property/riverside">View Details</a>
            <img src="https://www.gogettersmultifamily.com/images/riverside.jpg" alt="Riverside Apartments">
        </div>
    </div>
</body>
</html>
"""

class MockGoGettersScraper:
    """Mock version of the GoGetters scraper for testing."""
    
    def __init__(self):
        """Initialize the mock scraper."""
        self.base_url = "https://www.gogettersmultifamily.com"
        self.properties_url = f"{self.base_url}/current-listings"
    
    async def _extract_properties_from_html(self, html: str) -> List[Dict[str, Any]]:
        """
        Extract property listings from HTML content.
        This is the actual method from the real scraper that we want to test.
        
        Args:
            html: The HTML content to parse.
            
        Returns:
            A list of property information dictionaries.
        """
        properties = []
        
        # Import the real parsing logic
        from bs4 import BeautifulSoup
        import re
        
        # Parse HTML using BeautifulSoup
        try:
            soup = BeautifulSoup(html, 'html.parser')
            
            # Look for property cards
            property_cards = soup.select('.property-card, .listing-item, .property-item, article.property')
            
            if property_cards:
                logger.info(f"Found {len(property_cards)} property cards")
                
                # Extract properties with their details
                for card in property_cards:
                    try:
                        # Get property title
                        title_elem = card.select_one('h1, h2, h3, h4, h5, h6, .title, .property-title')
                        title = title_elem.get_text(strip=True) if title_elem else "Unlisted Property"
                        
                        # Get property link
                        link = ""
                        link_elem = card.select_one('a[href]')
                        if link_elem:
                            href = link_elem.get('href', '')
                            if href:
                                # Handle relative URLs
                                if href.startswith('/'):
                                    link = f"{self.base_url}{href}"
                                else:
                                    link = href
                        
                        # Get property image
                        image_url = ""
                        image_elem = card.select_one('img')
                        if image_elem:
                            src = image_elem.get('src', '') or image_elem.get('data-src', '')
                            if src:
                                # Handle relative URLs
                                if src.startswith('/'):
                                    image_url = f"{self.base_url}{src}"
                                else:
                                    image_url = src
                        
                        # Get property location
                        location = ""
                        location_elem = card.select_one('.location, .address, .property-location')
                        if location_elem:
                            location = location_elem.get_text(strip=True)
                        
                        # Get property description
                        description = ""
                        desc_elem = card.select_one('.description, .summary, .excerpt, .property-description')
                        if desc_elem:
                            description = desc_elem.get_text(strip=True)
                        
                        # Extract property details like units, price, etc.
                        card_text = card.get_text().lower()
                        
                        # Look for units info
                        units = ""
                        units_match = re.search(r'(\d+)\s*(?:unit|units)', card_text, re.IGNORECASE)
                        if units_match:
                            units = units_match.group(1)
                        
                        # Look for price info
                        price = ""
                        price_match = re.search(r'\$([\d,.]+)(?:\s*(?:million|m))?', card_text, re.IGNORECASE)
                        if price_match:
                            price = f"${price_match.group(1)}"
                            # Check if the price is in millions
                            if 'million' in price_match.group(0).lower() or 'm' in price_match.group(0).lower():
                                price += "M"
                        
                        # Look for property type
                        property_type = "Multifamily"  # Default since this is a multifamily-focused site
                        type_elem = card.select_one('.property-type, .type, .category')
                        if type_elem:
                            type_text = type_elem.get_text(strip=True)
                            if type_text:
                                property_type = type_text
                        
                        # Look for square footage
                        sq_ft = ""
                        sqft_match = re.search(r'([\d,]+)\s*(?:sq\.?\s*(?:ft|feet)|sf|square\s*feet)', card_text, re.IGNORECASE)
                        if sqft_match:
                            sq_ft = sqft_match.group(1).replace(',', '')
                        
                        # Look for status (e.g., Available, Under Contract)
                        status = "Available"  # Default
                        status_elem = card.select_one('.status, .property-status')
                        if status_elem:
                            status_text = status_elem.get_text(strip=True)
                            if status_text:
                                status = status_text
                        elif "under contract" in card_text:
                            status = "Under Contract"
                        elif "sold" in card_text:
                            status = "Sold"
                        
                        # Create property object
                        property_info = {
                            "title": title,
                            "description": description,
                            "link": link,
                            "location": location,
                            "units": units,
                            "property_type": property_type,
                            "price": price,
                            "sq_ft": sq_ft,
                            "status": status,
                            "image_url": image_url,
                            "source": "GoGetters Multifamily"
                        }
                        
                        properties.append(property_info)
                        logger.info(f"Extracted property: {title}")
                        
                    except Exception as e:
                        logger.error(f"Error extracting property details: {e}")
                        continue
            else:
                logger.warning("No property cards found with standard selectors")
        
        except Exception as e:
            logger.error(f"Error parsing HTML: {e}")
            properties = []
        
        return properties

async def run_mock_test():
    """Run the mock test."""
    logger.info("Starting mock test for GoGetters scraper")
    
    # Create a mock scraper
    scraper = MockGoGettersScraper()
    
    # Extract properties from the sample HTML
    properties = await scraper._extract_properties_from_html(SAMPLE_HTML)
    
    # Print results
    logger.info(f"Extracted {len(properties)} properties")
    
    for i, prop in enumerate(properties):
        logger.info(f"Property {i+1}:")
        for key, value in prop.items():
            logger.info(f"  {key}: {value}")
    
    # Save results to a file
    results = {
        "url": scraper.properties_url,
        "title": "GoGetters Multifamily - Current Listings",
        "analyzed_at": str(datetime.now()),
        "success": True,
        "properties": properties
    }
    
    os.makedirs("test_output/gogetters", exist_ok=True)
    
    with open("test_output/gogetters/mock_test_results.json", "w") as f:
        json.dump(results, f, indent=2)
    
    logger.info("Mock test completed")
    return results

if __name__ == "__main__":
    asyncio.run(run_mock_test()) 