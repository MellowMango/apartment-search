"""
Specialized scraper for GREA (Global Real Estate Advisors) website.
This scraper extracts property listings from https://grea.com/properties/
focusing on multifamily properties.
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


class GREAScraper:
    """
    Specialized scraper for GREA (Global Real Estate Advisors) website.
    """
    
    def __init__(self):
        """Initialize the GREA scraper."""
        self.client = MCPClient(base_url="http://localhost:3001")
        self.storage = ScraperDataStorage("grea", save_to_db=True)
        self.base_url = "https://grea.com"
        self.properties_url = f"{self.base_url}/properties/"
        
        # URL for multifamily properties specifically
        self.multifamily_url = f"{self.properties_url}?property-type=multifamily"
    
    async def extract_properties(self) -> Dict[str, Any]:
        """
        Extract property listings from the GREA website.
        
        Returns:
            A dictionary containing the extracted property information.
        """
        # Navigate to the multifamily properties page
        logger.info(f"Navigating to {self.multifamily_url}")
        navigation_success = await self.client.navigate_to_page(self.multifamily_url)
        if not navigation_success:
            logger.warning(f"Failed to navigate to multifamily URL, trying main properties URL")
            navigation_success = await self.client.navigate_to_page(self.properties_url)
            if not navigation_success:
                logger.error(f"Failed to navigate to {self.properties_url}")
                return {"success": False, "error": "Navigation failed"}
        
        # Wait for the property cards to load - this page likely uses JavaScript to load content
        logger.info("Waiting for property listings to load...")
        await asyncio.sleep(10)  # Give the page time to load dynamic content
        
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
            try:
                # Try the async method first (for the custom DataStorage class)
                await self.storage.save_screenshot(screenshot)
            except (AttributeError, TypeError):
                # Fall back to the non-async method or method with different signature
                if hasattr(self.storage, 'save_screenshot'):
                    if callable(getattr(self.storage, 'save_screenshot')):
                        self.storage.save_screenshot(screenshot, timestamp)
        
        # Save HTML content
        try:
            # Try the async method first (for the custom DataStorage class)
            html_path = await self.storage.save_html_content(html)
        except (AttributeError, TypeError):
            # Fall back to the non-async method or method with different signature
            if hasattr(self.storage, 'save_html'):
                if callable(getattr(self.storage, 'save_html')):
                    html_path = self.storage.save_html(html, timestamp)
            elif hasattr(self.storage, 'save_html_content'):
                if callable(getattr(self.storage, 'save_html_content')):
                    html_path = self.storage.save_html_content(html, timestamp)
        
        # Extract page title
        try:
            title = await self.client.execute_script("document.title")
            logger.info(f"Page title: {title}")
        except Exception as e:
            logger.error(f"Error getting page title: {e}")
            title = "GREA Properties"
        
        # Initialize results
        results = {
            "url": self.properties_url,
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
                await asyncio.sleep(8)
                
                # Get the HTML content
                html = await self.client.get_html()
                if not html:
                    logger.error(f"Failed to get HTML content for page {page_num}")
                    continue
                
                # Save HTML for debugging
                timestamp = datetime.now()
                try:
                    # Try the async method first (for the custom DataStorage class)
                    await self.storage.save_html_content(html)
                except (AttributeError, TypeError):
                    # Fall back to the non-async method or method with different signature
                    if hasattr(self.storage, 'save_html'):
                        if callable(getattr(self.storage, 'save_html')):
                            self.storage.save_html(html, timestamp)
                    elif hasattr(self.storage, 'save_html_content'):
                        if callable(getattr(self.storage, 'save_html_content')):
                            self.storage.save_html_content(html, timestamp)
                
                # Extract properties from this page
                page_properties = await self._extract_properties_from_html(html)
                logger.info(f"Extracted {len(page_properties)} properties from page {page_num}")
                results["properties"].extend(page_properties)
        except Exception as e:
            logger.error(f"Error processing pagination: {e}")
            # Continue with the properties we have from the first page
        
        # Save the extracted data
        try:
            # Try the async method first (for the custom DataStorage class)
            await self.storage.save_extracted_data(results["properties"])
        except (AttributeError, TypeError):
            # Fall back to the non-async method or method with different signature
            if hasattr(self.storage, 'save_extracted_data'):
                if callable(getattr(self.storage, 'save_extracted_data')):
                    try:
                        self.storage.save_extracted_data(results, "properties", timestamp)
                    except TypeError:
                        self.storage.save_extracted_data(results)
        
        # Save to database
        if results["properties"]:
            logger.info(f"Saving {len(results['properties'])} properties to database")
            try:
                # Try the async method first (for the custom DataStorage class)
                await self.storage.save_to_database(results["properties"])
            except (AttributeError, TypeError):
                # Fall back to the non-async method
                if hasattr(self.storage, 'save_to_database'):
                    if callable(getattr(self.storage, 'save_to_database')):
                        self.storage.save_to_database(results["properties"])
        
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
            
            # Look for pagination elements
            pagination_elem = soup.select('.pagination')
            if pagination_elem:
                pagination = pagination_elem[0]
                page_links = pagination.select('a')
                if page_links:
                    # Last page number might be in the last link or second to last (if last is "Next")
                    page_numbers = []
                    for link in page_links:
                        text = link.text.strip()
                        if text.isdigit():
                            page_numbers.append(int(text))
                    
                    if page_numbers:
                        return max(page_numbers)
            
            # Try to execute JavaScript to get pagination info
            try:
                pagination_script = """
                    try {
                        // Try to find pagination info in various forms
                        const paginationEl = document.querySelector('.pagination');
                        if (paginationEl) {
                            const pageLinks = paginationEl.querySelectorAll('a');
                            const pageNums = Array.from(pageLinks)
                                .map(a => parseInt(a.textContent.trim()))
                                .filter(num => !isNaN(num));
                            if (pageNums.length > 0) {
                                return Math.max(...pageNums);
                            }
                        }
                        
                        // Check if there's pagination info in the DOM
                        const pageInfo = document.querySelector('[data-total-pages]');
                        if (pageInfo) {
                            return parseInt(pageInfo.getAttribute('data-total-pages'));
                        }
                        
                        return 1;
                    } catch (e) {
                        console.error(e);
                        return 1;
                    }
                """
                total_pages = await self.client.execute_script(pagination_script)
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
            page_url = f"{self.properties_url}page/{page_num}/"
            if "property-type=multifamily" in self.multifamily_url:
                page_url = f"{self.properties_url}page/{page_num}/?property-type=multifamily"
            
            # Try clicking the pagination link first
            next_page_script = f"""
                try {{
                    // Look for pagination links
                    const paginationLinks = document.querySelectorAll('.pagination a');
                    let targetLink = null;
                    
                    // Find link with page number
                    for (const link of paginationLinks) {{
                        if (link.textContent.trim() === "{page_num}") {{
                            targetLink = link;
                            break;
                        }}
                    }}
                    
                    // If found, click it
                    if (targetLink) {{
                        targetLink.click();
                        return true;
                    }}
                    
                    // If not found, try clicking "Next" button
                    const nextBtn = Array.from(paginationLinks).find(link => 
                        link.textContent.trim().toLowerCase() === "next" || 
                        link.textContent.trim() === "›" ||
                        link.innerHTML.includes("next") ||
                        link.getAttribute("aria-label") === "Next"
                    );
                    
                    if (nextBtn) {{
                        nextBtn.click();
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
            
            # Look for property cards - try different possible class names/selectors
            property_cards = soup.select('.property-card, .listing-item, .property, article.property')
            
            if not property_cards:
                # Try more generic selectors
                property_cards = soup.select('.property-listing, .listing, .property-item')
                
            if not property_cards:
                # Try to identify any elements that might be property listings
                property_cards = soup.find_all(['div', 'li', 'article'], class_=lambda c: c and any(x in str(c).lower() for x in ['property', 'listing', 'estate-item']))
                
            if property_cards:
                logger.info(f"Found {len(property_cards)} property cards")
                
                # Extract properties with their details
                for card in property_cards:
                    try:
                        # Check if this is a multifamily property
                        card_text = card.get_text().lower()
                        property_type = "Unknown"
                        
                        # Try to determine property type
                        type_elem = card.select_one('.property-type, .type, .category')
                        if type_elem:
                            property_type = type_elem.get_text(strip=True)
                        elif "apartment" in card_text or "multifamily" in card_text:
                            property_type = "Multifamily"
                        
                        # Skip if not a multifamily property and we're filtering
                        if "property-type=multifamily" in self.multifamily_url and not (
                            "multifamily" in property_type.lower() or 
                            "apartment" in property_type.lower() or
                            "multi-family" in property_type.lower() or
                            "multi family" in property_type.lower()
                        ):
                            continue
                        
                        # Get property title
                        title = "Unlisted Property"
                        title_elem = card.select_one('h2, h3, h4, .title, .property-title')
                        if title_elem:
                            title = title_elem.get_text(strip=True)
                        
                        # Get property link
                        link = ""
                        link_elem = card.select_one('a')
                        if link_elem:
                            href = link_elem.get('href', '')
                            if href:
                                # Handle relative URLs
                                if href.startswith('/'):
                                    link = f"{self.base_url}{href}"
                                else:
                                    link = href
                        
                        # Get property location
                        location = ""
                        location_elem = card.select_one('.location, .address, .property-location')
                        if location_elem:
                            location = location_elem.get_text(strip=True)
                        
                        # Get property description
                        description = ""
                        desc_elem = card.select_one('.description, .summary, .property-description')
                        if desc_elem:
                            description = desc_elem.get_text(strip=True)
                        
                        # Get property image
                        image_url = ""
                        image_elem = card.select_one('img')
                        if image_elem:
                            src = image_elem.get('src', '')
                            data_src = image_elem.get('data-src', '')
                            if data_src:  # Some sites use data-src for lazy loading
                                src = data_src
                            if src:
                                # Handle relative URLs
                                if src.startswith('/'):
                                    image_url = f"{self.base_url}{src}"
                                else:
                                    image_url = src
                        
                        # Extract property details like units, price, etc.
                        units = ""
                        price = ""
                        sq_ft = ""
                        
                        # Look for units info
                        units_regex = r'(\d+)\s*(?:unit|units)'
                        units_match = re.search(units_regex, card_text, re.IGNORECASE)
                        if units_match:
                            units = units_match.group(1)
                        
                        # Look for price info
                        price_regex = r'\$([\d,.]+)(?:\s*(?:million|m))?'
                        price_match = re.search(price_regex, card_text, re.IGNORECASE)
                        if price_match:
                            price = f"${price_match.group(1)}"
                            # Check if the price is in millions
                            if price_match.group(0).lower().endswith('m') or 'million' in price_match.group(0).lower():
                                price += "M"
                        
                        # Look for square footage
                        sqft_regex = r'([\d,]+)\s*(?:sq\.?\s*(?:ft|feet)|sf|square\s*feet)'
                        sqft_match = re.search(sqft_regex, card_text, re.IGNORECASE)
                        if sqft_match:
                            sq_ft = sqft_match.group(1).replace(',', '')
                        
                        # Look for status
                        status = "Available"
                        status_elem = card.select_one('.status, .property-status')
                        if status_elem:
                            status = status_elem.get_text(strip=True)
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
                            "source": "GREA"
                        }
                        
                        properties.append(property_info)
                        logger.debug(f"Extracted property: {title}")
                        
                    except Exception as e:
                        logger.error(f"Error extracting property details: {e}")
                        continue
                
                logger.info(f"Extracted {len(properties)} properties")
            else:
                logger.warning("No property cards found with standard selectors")
                
                # Try an alternative approach - look for any sections that might contain property data
                sections = soup.find_all(['section', 'div'], class_=lambda c: c and any(x in str(c).lower() for x in ['properties', 'listings', 'search-results']))
                
                if sections:
                    logger.info(f"Trying alternative extraction from {len(sections)} sections")
                    
                    for section in sections:
                        # Look for links to property pages
                        links = section.find_all('a', href=True)
                        
                        for link in links:
                            try:
                                href = link.get('href', '')
                                if not href or href == '#' or 'javascript:' in href:
                                    continue
                                
                                # Check if this might be a property link
                                link_text = link.get_text().lower()
                                if not any(x in link_text or x in href.lower() for x in ['property', 'listing', 'sale', 'leasing', 'apartment', 'multifamily']):
                                    continue
                                
                                # Handle relative URLs
                                full_url = href
                                if href.startswith('/'):
                                    full_url = f"{self.base_url}{href}"
                                
                                # Get title
                                title = link.get_text(strip=True) or "Unlisted Property"
                                
                                # Try to find an associated image
                                image_url = ""
                                parent = link.parent
                                for _ in range(3):  # Check up to 3 levels up
                                    if parent:
                                        img = parent.find('img')
                                        if img:
                                            src = img.get('src', '') or img.get('data-src', '')
                                            if src:
                                                if src.startswith('/'):
                                                    image_url = f"{self.base_url}{src}"
                                                else:
                                                    image_url = src
                                            break
                                        parent = parent.parent
                                    else:
                                        break
                                
                                # Create minimal property object
                                property_info = {
                                    "title": title,
                                    "description": "",
                                    "link": full_url,
                                    "location": "",
                                    "units": "",
                                    "property_type": "Multifamily",
                                    "price": "",
                                    "sq_ft": "",
                                    "status": "Available",
                                    "image_url": image_url,
                                    "source": "GREA"
                                }
                                
                                properties.append(property_info)
                                logger.debug(f"Extracted property from link: {title}")
                                
                            except Exception as e:
                                logger.error(f"Error extracting property from link: {e}")
                                continue
        
        except Exception as e:
            logger.error(f"Error parsing HTML: {e}")
            properties = []
        
        return properties


async def main():
    """Run the GREA scraper."""
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
    
    scraper = GREAScraper()
    results = await scraper.extract_properties()
    
    if results.get("success"):
        logger.info(f"Successfully extracted {len(results.get('properties', []))} properties")
    else:
        logger.error(f"Failed to extract properties: {results.get('error')}")


if __name__ == "__main__":
    asyncio.run(main())
