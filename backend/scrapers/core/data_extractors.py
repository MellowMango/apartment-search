"""
Common data extraction utilities for web scraping.
"""

import re
import logging
from typing import Dict, Any, List, Optional
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

def extract_property_listings_from_html(html: str, 
                                      property_title_selector: str = '.property-title, .listing-title, .property-name',
                                      property_description_selector: str = '.property-description, .listing-description',
                                      property_link_selector: str = 'a[href*="property"], a[href*="listing"]') -> List[Dict[str, Any]]:
    """
    Extract property listings from HTML using BeautifulSoup.
    
    Args:
        html: The HTML content to parse.
        property_title_selector: CSS selector for property titles.
        property_description_selector: CSS selector for property descriptions.
        property_link_selector: CSS selector for property links.
    
    Returns:
        A list of dictionaries containing property information.
    """
    if not html:
        logger.warning("No HTML content provided for extraction")
        return []
    
    try:
        soup = BeautifulSoup(html, 'html.parser')
        
        # Find property elements
        properties = []
        
        # Try to find property elements using the provided selectors
        title_elements = soup.select(property_title_selector)
        description_elements = soup.select(property_description_selector)
        link_elements = soup.select(property_link_selector)
        
        # If we found titles, use them as the basis for properties
        if title_elements:
            for i, title_element in enumerate(title_elements):
                property_info = {
                    "title": title_element.get_text(strip=True),
                    "description": "",
                    "link": "",
                    "address": "",
                    "price": "",
                    "units": "",
                    "sqft": "",
                    "year_built": ""
                }
                
                # Try to find a matching description
                for desc_element in description_elements:
                    if title_element in desc_element.parents or desc_element in title_element.parents:
                        property_info["description"] = desc_element.get_text(strip=True)
                        break
                
                # Try to find a matching link
                for link_element in link_elements:
                    if title_element in link_element.parents or link_element in title_element.parents:
                        property_info["link"] = link_element.get('href', '')
                        break
                
                # Extract additional property information from text
                full_text = property_info["title"] + " " + property_info["description"]
                
                # Extract address
                address_match = re.search(r'(?:Address|Location):\s*([^,]+(?:,\s*[^,]+){1,3})', full_text, re.IGNORECASE)
                if address_match:
                    property_info["address"] = address_match.group(1).strip()
                
                # Extract price
                price_match = re.search(r'(?:Price|Asking):\s*\$?([\d,]+(?:\.\d+)?)', full_text, re.IGNORECASE)
                if price_match:
                    property_info["price"] = price_match.group(1).strip()
                
                # Extract units
                units_match = re.search(r'(?:Units|Unit count|# of units):\s*(\d+)', full_text, re.IGNORECASE)
                if units_match:
                    property_info["units"] = units_match.group(1).strip()
                
                # Extract square footage
                sqft_match = re.search(r'(?:Sq(uare)?\s*[Ff](ee)?t|Sqft):\s*([\d,]+)', full_text, re.IGNORECASE)
                if sqft_match:
                    property_info["sqft"] = sqft_match.group(3).strip()
                
                # Extract year built
                year_match = re.search(r'(?:Year built|Built):\s*(\d{4})', full_text, re.IGNORECASE)
                if year_match:
                    property_info["year_built"] = year_match.group(1).strip()
                
                properties.append(property_info)
        
        return properties
    
    except Exception as e:
        logger.error(f"Error extracting property listings from HTML: {e}")
        return [] 