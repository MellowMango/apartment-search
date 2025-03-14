"""
Specialized scraper for nmrk (Newmark) website.
This scraper extracts property listings from https://www.nmrk.com/properties/investment-sales
with a focus on multifamily properties.
"""

import asyncio
import logging
import re
import json
from datetime import datetime
from typing import Dict, Any, List, Optional

from bs4 import BeautifulSoup

from backend.scrapers.core.mcp_client import MCPClient
from backend.scrapers.core.storage import ScraperDataStorage

logger = logging.getLogger(__name__)


class NmrkScraper:
    """
    Specialized scraper for Newmark website, focusing on multifamily properties.
    """
    
    def __init__(self):
        """Initialize the Newmark scraper."""
        self.client = MCPClient()
        self.storage = ScraperDataStorage("nmrk", save_to_db=True)
        self.base_url = "https://www.nmrk.com"
        self.properties_url = f"{self.base_url}/properties/investment-sales"
        
        # Add a URL for multifamily properties specifically
        self.multifamily_url = f"{self.properties_url}?propertyType=Multifamily&tab=properties"
    
    async def extract_properties(self) -> Dict[str, Any]:
        """
        Extract property listings from the Newmark website.
        
        Returns:
            A dictionary containing the extracted property information.
        """
        # Navigate to the multifamily properties page
        logger.info(f"Navigating to {self.multifamily_url}")
        navigation_success = await self.client.navigate_to_page(self.multifamily_url)
        if not navigation_success:
            logger.error(f"Failed to navigate to {self.multifamily_url}")
            return {"success": False, "error": "Navigation failed"}
        
        # Wait for the property cards to load - this page likely uses JavaScript to load content
        logger.info("Waiting for property listings to load...")
        await asyncio.sleep(12)  # Give the page more time to load dynamic content
        
        # Get the HTML content
        logger.info("Getting HTML content")
        html = await self.client.get_html()
        if not html:
            logger.error("Failed to get HTML content")
            return {"success": False, "error": "Failed to get HTML"}
        
        # Take a screenshot
        logger.info("Taking screenshot")
        screenshot = await self.client.take_screenshot()
        timestamp = datetime.now()
        
        # Save data to files
        if screenshot:
            self.storage.save_screenshot(screenshot, timestamp)
        
        html_path = self.storage.save_html(html, timestamp)
        
        # Extract page title
        try:
            title = await self.client.execute_script("document.title")
            logger.info(f"Page title: {title}")
        except Exception as e:
            logger.error(f"Error getting page title: {e}")
            title = "Newmark Investment Sales Properties"
        
        # Initialize results
        results = {
            "url": self.multifamily_url,
            "title": title,
            "analyzed_at": str(timestamp),
            "success": True,
            "properties": []
        }
        
        # Extract properties from the first page
        properties = await self._extract_properties_from_html(html)
        logger.info(f"Extracted {len(properties)} properties from first page")
        results["properties"].extend(properties)
        
        # Check for pagination and process additional pages if available
        try:
            total_pages = await self._get_total_pages(html)
            logger.info(f"Found {total_pages} pages of properties")
            
            # Process pages 2 to total_pages
            for page_num in range(2, total_pages + 1):
                logger.info(f"Processing page {page_num} of {total_pages}")
                # Navigate to the next page
                next_page_success = await self._navigate_to_page(page_num)
                if not next_page_success:
                    logger.error(f"Failed to navigate to page {page_num}")
                    continue
                
                # Wait for the page to load
                await asyncio.sleep(10)
                
                # Get the HTML content
                html = await self.client.get_html()
                if not html:
                    logger.error(f"Failed to get HTML content for page {page_num}")
                    continue
                
                # Save HTML for debugging
                timestamp = datetime.now()
                self.storage.save_html(html, timestamp)
                
                # Extract properties from this page
                page_properties = await self._extract_properties_from_html(html)
                logger.info(f"Extracted {len(page_properties)} properties from page {page_num}")
                results["properties"].extend(page_properties)
        except Exception as e:
            logger.error(f"Error processing pagination: {e}")
            # Continue with the properties we have from the first page
        
        # Save the extracted data
        self.storage.save_extracted_data(results, "properties", timestamp)
        
        # Save to database
        if results["properties"]:
            logger.info(f"Saving {len(results['properties'])} properties to database")
            await self.storage.save_to_database(results["properties"])
        
        logger.info(f"Total properties extracted: {len(results['properties'])}")
        return results

    async def _get_total_pages(self, html: str) -> int:
        """
        Extract the total number of pages from the pagination element.
        
        Args:
            html: The HTML content of the page.
            
        Returns:
            The total number of pages.
        """
        try:
            soup = BeautifulSoup(html, 'html.parser')
            
            # Look for pagination element with total pages info
            # Check for specific page total element
            total_pages_elem = soup.select_one('#rcmPagingGotoPageTotal')
            if total_pages_elem:
                total_pages_text = total_pages_elem.text.strip()
                if total_pages_text.isdigit():
                    return int(total_pages_text)
            
            # Try to find pagination links
            pagination_links = soup.select('.rcmPagingGotoPage')
            if pagination_links:
                try:
                    # Try to extract using JavaScript
                    pages_script = """
                        try {
                            const pagerTotal = document.querySelector('#rcmPagingGotoPageTotal');
                            if (pagerTotal) {
                                return parseInt(pagerTotal.textContent.trim());
                            }
                            return 1;
                        } catch (e) {
                            return 1;
                        }
                    """
                    total_pages = await self.client.execute_script(pages_script)
                    if isinstance(total_pages, int) and total_pages > 0:
                        return total_pages
                except Exception as e:
                    logger.error(f"Error executing pagination script: {e}")
            
            # Default to 1 page if no pagination found
            return 1
            
        except Exception as e:
            logger.error(f"Error parsing total pages: {e}")
            return 1
    
    async def _navigate_to_page(self, page_num: int) -> bool:
        """
        Navigate to a specific page in the pagination.
        
        Args:
            page_num: The page number to navigate to.
            
        Returns:
            True if navigation was successful, False otherwise.
        """
        try:
            # Construct the URL for the specific page
            page_url = f"{self.multifamily_url}&pg={page_num}"
            
            # Try clicking the next page button
            next_page_script = f"""
                try {{
                    // First try with page goto input
                    const pageInput = document.querySelector('#rcmPagingGotoPageText');
                    if (pageInput) {{
                        pageInput.value = "{page_num}";
                        const event = new Event('change', {{ bubbles: true }});
                        pageInput.dispatchEvent(event);
                        
                        // Try to trigger the goto function
                        if (window._engine && window._engine.GotoPage) {{
                            window._engine.GotoPage();
                            return true;
                        }}
                    }}
                    
                    // If that fails, try next button
                    const nextButton = document.querySelector('#rcmPagingNext');
                    if (nextButton) {{
                        nextButton.click();
                        return true;
                    }}
                    
                    return false;
                }} catch (e) {{
                    console.error(e);
                    return false;
                }}
            """
            
            # Try using JavaScript to navigate
            nav_success = await self.client.execute_script(next_page_script)
            if nav_success:
                logger.info(f"Successfully navigated to page {page_num} via JavaScript")
                return True
            
            # If JavaScript navigation fails, try direct URL
            logger.info(f"JavaScript navigation failed, trying direct URL: {page_url}")
            return await self.client.navigate_to_page(page_url)
            
        except Exception as e:
            logger.error(f"Error navigating to page {page_num}: {e}")
            return False
    
    async def _extract_properties_from_html(self, html: str) -> List[Dict[str, Any]]:
        """
        Extract property listings from HTML content.
        
        Args:
            html: The HTML content to parse.
            
        Returns:
            A list of property information dictionaries.
        """
        properties = []
        
        # Parse HTML using BeautifulSoup
        try:
            soup = BeautifulSoup(html, 'html.parser')
            
            # Look for RCM property cards - based on the actual HTML structure
            property_cards = soup.select('.rcm_card')
            
            if not property_cards:
                # Fallback to other potential selectors if rcm_card isn't found
                property_cards = soup.find_all(['div', 'article', 'li'], class_=lambda c: c and any(x in c.lower() for x in ['property-card', 'property-item', 'property-listing', 'listing-item', 'rcm_card']))
            
            if not property_cards:
                # Try more generic selectors if specific ones don't work
                property_cards = soup.select('.properties-list .property, .results-list .result-item, .search-results .property')
            
            if property_cards:
                logger.info(f"Found {len(property_cards)} property cards")
                
                # Extract properties with their details
                for card in property_cards:
                    try:
                        # Extract property type
                        property_type = ""
                        type_elem = card.select_one('.asset-type')
                        if type_elem:
                            property_type = type_elem.text.strip()
                        
                        # Only process multifamily properties if property type is available
                        if property_type and "multifamily" not in property_type.lower():
                            logger.debug(f"Skipping non-multifamily property: {property_type}")
                            continue
                        
                        # Get property title/headline
                        title = "Unlisted Property"
                        title_elem = card.select_one('.headline a')
                        if title_elem:
                            title = title_elem.text.strip()
                        
                        # Get property link
                        link = ""
                        link_elem = card.select_one('.headline a')
                        if link_elem:
                            href = link_elem.get('href', '')
                            if href:
                                link = href  # Use the full URL as it appears to be absolute
                        
                        # Get property location (address and city)
                        address = ""
                        address_elem = card.select_one('.address a')
                        if address_elem:
                            address = address_elem.text.strip()
                        
                        city_state = ""
                        city_elem = card.select_one('.city a')
                        if city_elem:
                            city_state = city_elem.text.strip()
                        
                        location = f"{address}, {city_state}".strip().rstrip(',')
                        
                        # Get property description/summary
                        description = ""
                        desc_elem = card.select_one('.summary a p')
                        if desc_elem:
                            description = desc_elem.text.strip()
                        
                        # Get property image
                        image_url = ""
                        image_elem = card.select_one('.img-responsive')
                        if image_elem:
                            src = image_elem.get('src', '')
                            if src:
                                image_url = src
                        
                        # Extract units if available
                        units = ""
                        units_elem = card.select_one('.asset-units')
                        if units_elem:
                            units_text = units_elem.text.strip()
                            units_match = re.search(r'(\d+)\s*Units', units_text, re.IGNORECASE)
                            if units_match:
                                units = units_match.group(1)
                        
                        # Extract price if available
                        price = ""
                        price_elem = card.select_one('.price')
                        if price_elem:
                            price = price_elem.text.strip()
                        
                        # Extract square footage if available
                        sq_ft = ""
                        sqft_elem = card.select_one('.asset-sqft')
                        if sqft_elem:
                            sqft_text = sqft_elem.text.strip()
                            sqft_match = re.search(r'([\d,]+)\s*sq ft', sqft_text, re.IGNORECASE)
                            if sqft_match:
                                sq_ft = sqft_match.group(1).replace(',', '')
                        
                        # Extract contact information
                        contacts = []
                        contact_elems = card.select('.contact')
                        for contact_elem in contact_elems:
                            name_elem = contact_elem.select_one('.name a')
                            phone_elem = contact_elem.select_one('.phone a')
                            email_elem = contact_elem.select_one('.email a')
                            
                            contact_info = {}
                            if name_elem:
                                contact_info['name'] = name_elem.text.strip()
                            if phone_elem:
                                phone_text = phone_elem.text.strip()
                                # Remove any icons or extra text
                                phone_match = re.search(r'[\d\-\+\(\)\s]+', phone_text)
                                if phone_match:
                                    contact_info['phone'] = phone_match.group(0).strip()
                            if email_elem:
                                email = email_elem.get('href', '').replace('mailto:', '')
                                if email:
                                    contact_info['email'] = email
                            
                            if contact_info:
                                contacts.append(contact_info)
                        
                        # Status (default to Available)
                        status = "Available"
                        status_elem = card.select_one('.status-bar-wrapper')
                        if status_elem and status_elem.text.strip():
                            status = status_elem.text.strip()
                        
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
                            "contacts": contacts
                        }
                        
                        properties.append(property_info)
                        logger.debug(f"Extracted property: {title}")
                        
                    except Exception as e:
                        logger.error(f"Error extracting property details: {e}")
                        continue
                
                logger.info(f"Extracted {len(properties)} properties")
            else:
                logger.warning("No property cards found with standard selectors")
                
                # Try an alternative approach: look for any section that might contain property listings
                sections = soup.find_all('section') or soup.find_all('div', class_=lambda c: c and 'section' in c.lower())
                
                if sections:
                    logger.info(f"Found {len(sections)} sections to check for properties")
                    
                    # Try to extract from each section
                    all_properties = []
                    
                    for section in sections:
                        # Check for link elements that might point to property details
                        links = section.find_all('a', href=True)
                        
                        # Filter links that might be property links
                        property_links = [link for link in links if re.search(r'(property|listing|sale|investment)', link.get('href', ''), re.IGNORECASE)]
                        
                        if property_links:
                            logger.info(f"Found {len(property_links)} potential property links in a section")
                            
                            for link in property_links:
                                try:
                                    # Get the URL
                                    href = link.get('href', '')
                                    if not href:
                                        continue
                                    
                                    # Handle relative URLs
                                    full_url = href
                                    if href.startswith('/'):
                                        full_url = f"{self.base_url}{href}"
                                    
                                    # Get title from the link text or img alt text
                                    link_text = link.get_text(strip=True)
                                    title = link_text if link_text else "Unlisted Property"
                                    
                                    if not link_text:
                                        img = link.find('img')
                                        if img and img.get('alt'):
                                            title = img.get('alt')
                                    
                                    # Create a minimal property object
                                    property_info = {
                                        "title": title,
                                        "description": "",
                                        "link": full_url,
                                        "location": "",
                                        "units": "",
                                        "year_built": "",
                                        "status": "Available",
                                        "price": "",
                                        "image_url": ""
                                    }
                                    
                                    all_properties.append(property_info)
                                    logger.debug(f"Extracted property from link: {title}")
                                    
                                except Exception as e:
                                    logger.error(f"Error extracting property from link: {e}")
                                    continue
                    
                    if all_properties:
                        properties = all_properties
                        logger.info(f"Extracted {len(properties)} properties from alternative approach")
                    else:
                        logger.warning("No properties found with alternative approach")
                else:
                    logger.warning("No sections found to check for properties")
        
        except Exception as e:
            logger.error(f"Error parsing HTML: {e}")
            properties = []
        
        return properties


async def main():
    """Run the nmrk scraper."""
    logging.basicConfig(level=logging.INFO, 
                      format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # Check for required environment variables
    import os
    from dotenv import load_dotenv
    
    # Load environment variables
    load_dotenv()
    
    # Check database credentials
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    neo4j_uri = os.getenv("NEO4J_URI")
    neo4j_user = os.getenv("NEO4J_USERNAME")
    neo4j_pass = os.getenv("NEO4J_PASSWORD")
    
    # Print available database connections
    db_connections = []
    if supabase_url and supabase_key:
        db_connections.append("Supabase")
    if neo4j_uri and neo4j_user and neo4j_pass:
        db_connections.append("Neo4j")
    
    if db_connections:
        logger.info(f"Database connections available: {', '.join(db_connections)}")
    else:
        logger.warning("No database credentials found. Data will be saved to files only. "
                      "To enable database storage, set the required environment variables.")
    
    scraper = NmrkScraper()
    results = await scraper.extract_properties()
    
    if results.get("success"):
        logger.info(f"Successfully extracted {len(results.get('properties', []))} properties")
    else:
        logger.error(f"Failed to extract properties: {results.get('error')}")


if __name__ == "__main__":
    asyncio.run(main())
