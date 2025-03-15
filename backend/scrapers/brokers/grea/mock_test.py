"""
Mock test for the GREA scraper.
This script tests the property extraction logic using a sample HTML.
"""

import asyncio
import logging
import json
import os
from datetime import datetime
from typing import Dict, Any, List

from bs4 import BeautifulSoup

from backend.scrapers.brokers.grea.scraper import GREAScraper

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Sample HTML for testing
SAMPLE_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>GREA Properties</title>
</head>
<body>
    <div class="properties-container">
        <!-- Property 1 -->
        <div class="property-card">
            <div class="property-image">
                <img src="https://grea.com/images/property1.jpg" alt="Property 1">
            </div>
            <div class="property-details">
                <h3 class="property-title">Luxury Apartment Complex</h3>
                <p class="property-location">Miami, FL</p>
                <p class="property-type">Multifamily</p>
                <p class="property-description">Beautiful 120-unit luxury apartment complex in prime location.</p>
                <p class="property-price">$25,000,000</p>
                <p class="property-info">120 units | 150,000 sq ft</p>
                <p class="property-status">Available</p>
                <a href="https://grea.com/properties/luxury-apartment-complex" class="property-link">View Details</a>
            </div>
        </div>
        
        <!-- Property 2 -->
        <div class="property-card">
            <div class="property-image">
                <img src="https://grea.com/images/property2.jpg" alt="Property 2">
            </div>
            <div class="property-details">
                <h3 class="property-title">Downtown Lofts</h3>
                <p class="property-location">Atlanta, GA</p>
                <p class="property-type">Multifamily</p>
                <p class="property-description">Modern loft apartments in downtown with 85 units.</p>
                <p class="property-price">$18,500,000</p>
                <p class="property-info">85 units | 95,000 sq ft</p>
                <p class="property-status">Under Contract</p>
                <a href="https://grea.com/properties/downtown-lofts" class="property-link">View Details</a>
            </div>
        </div>
        
        <!-- Property 3 -->
        <div class="property-card">
            <div class="property-image">
                <img src="https://grea.com/images/property3.jpg" alt="Property 3">
            </div>
            <div class="property-details">
                <h3 class="property-title">Riverside Apartments</h3>
                <p class="property-location">Dallas, TX</p>
                <p class="property-type">Multifamily</p>
                <p class="property-description">Riverside apartment complex with 60 units and river views.</p>
                <p class="property-price">$12,000,000</p>
                <p class="property-info">60 units | 75,000 sq ft</p>
                <p class="property-status">Available</p>
                <a href="https://grea.com/properties/riverside-apartments" class="property-link">View Details</a>
            </div>
        </div>
    </div>
    
    <div class="pagination">
        <a href="#" class="active">1</a>
        <a href="#">2</a>
        <a href="#">3</a>
        <a href="#">Next</a>
    </div>
</body>
</html>
"""


class MockGREAScraper(GREAScraper):
    """Mock version of the GREA scraper for testing."""
    
    async def extract_properties(self) -> Dict[str, Any]:
        """
        Extract properties from the sample HTML.
        
        Returns:
            A dictionary containing the extracted property information.
        """
        logger.info("Extracting properties from sample HTML")
        
        # Initialize results
        timestamp = datetime.now()
        results = {
            "url": self.properties_url,
            "title": "GREA Properties",
            "analyzed_at": str(timestamp),
            "success": True,
            "properties": []
        }
        
        # Extract properties from the sample HTML
        properties = await self._extract_properties_from_html(SAMPLE_HTML)
        logger.info(f"Extracted {len(properties)} properties from sample HTML")
        results["properties"].extend(properties)
        
        # Save the extracted data to file
        output_dir = os.path.join("test_output", "grea")
        os.makedirs(output_dir, exist_ok=True)
        
        timestamp_str = timestamp.strftime("%Y%m%d-%H%M%S")
        filename = os.path.join(output_dir, f"properties-{timestamp_str}.json")
        
        with open(filename, "w") as f:
            json.dump(results, f, indent=2)
        
        logger.info(f"Extracted data saved to {filename}")
        
        logger.info(f"Total properties extracted: {len(results['properties'])}")
        return results


async def run_mock_test():
    """Run the mock test for the GREA scraper."""
    logger.info("Starting GREA mock test")
    
    # Create the mock scraper
    scraper = MockGREAScraper()
    
    # Extract properties
    results = await scraper.extract_properties()
    
    # Check if extraction was successful
    if results.get("success"):
        properties = results.get("properties", [])
        logger.info(f"Successfully extracted {len(properties)} properties from sample HTML")
        
        # Log details of the properties
        for i, prop in enumerate(properties):
            logger.info(f"Property #{i+1}:")
            logger.info(f"  Title: {prop.get('title')}")
            logger.info(f"  Description: {prop.get('description')}")
            logger.info(f"  Link: {prop.get('link')}")
            logger.info(f"  Location: {prop.get('location')}")
            logger.info(f"  Units: {prop.get('units')}")
            logger.info(f"  Property Type: {prop.get('property_type')}")
            logger.info(f"  Price: {prop.get('price')}")
            logger.info(f"  Square Footage: {prop.get('sq_ft')}")
            logger.info(f"  Status: {prop.get('status')}")
            logger.info(f"  Image URL: {prop.get('image_url')}")
            logger.info(f"  Source: {prop.get('source')}")
    else:
        logger.error(f"Failed to extract properties: {results.get('error')}")


if __name__ == "__main__":
    asyncio.run(run_mock_test()) 