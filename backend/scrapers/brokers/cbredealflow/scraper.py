#!/usr/bin/env python3
"""
Scraper for CBRE DealFlow.
"""

import asyncio
import logging
import re
import json
import os
from datetime import datetime
from typing import Dict, Any, List, Optional

from bs4 import BeautifulSoup

from backend.scrapers.core.base_scraper import BaseScraper
from backend.scrapers.core.mcp_client import MCPClient
from backend.scrapers.core.storage import ScraperDataStorage

logger = logging.getLogger(__name__)


class CBREDealFlowScraper(BaseScraper):
    """
    Scraper for CBRE DealFlow website.
    """
    
    def __init__(self):
        """Initialize the scraper."""
        super().__init__()
        
        # Set up URLs
        self.base_url = "https://www.cbredealflow.com"
        self.properties_url = "https://www.cbredealflow.com"
        self.login_url = "https://www.cbredealflow.com/partner/portal/Login/Login.aspx"
        
        # Set up credentials
        self.username = os.getenv("CBREDEALFLOW_USERNAME", "")
        self.password = os.getenv("CBREDEALFLOW_PASSWORD", "")
        self.has_credentials = bool(self.username and self.password)
        
        # Initialize client and storage
        self.client = None
        self.storage = ScraperDataStorage("cbredealflow", save_to_db=True)
    
    async def login(self, browser_client) -> bool:
        """
        Log in to CBRE DealFlow.
        
        Returns:
            True if login was successful, False otherwise
        """
        if not self.has_credentials:
            logger.warning("No credentials provided for CBRE DealFlow. Cannot log in.")
            return False
        
        logger.info(f"Navigating to login page: {self.login_url}")
        navigation_success = await browser_client.navigate_to_page(self.login_url)
        if not navigation_success:
            logger.error(f"Failed to navigate to login page: {self.login_url}")
            return False
        
        # Wait for the page to load
        logger.info("Waiting for login page to load...")
        await asyncio.sleep(5)
        
        # Fill in login form and submit
        login_script = f"""
            try {{
                // Find username and password fields
                const usernameField = document.querySelector('input[type="email"], input[name*="email"], input[name*="username"], input[id*="email"], input[id*="username"]');
                const passwordField = document.querySelector('input[type="password"], input[name*="password"], input[id*="password"]');
                const loginButton = document.querySelector('button[type="submit"], input[type="submit"], button:contains("Sign In"), button:contains("Log In"), a:contains("Sign In"), a:contains("Log In")');
                
                if (usernameField && passwordField && loginButton) {{
                    // Fill in credentials
                    usernameField.value = "{self.username}";
                    passwordField.value = "{self.password}";
                    
                    // Submit form
                    console.log('Submitting login form');
                    loginButton.click();
                    return true;
                }} else {{
                    console.error('Could not find login form elements');
                    return false;
                }}
            }} catch (e) {{
                console.error('Error during login:', e);
                return false;
            }}
        """
        
        try:
            login_result = await browser_client.execute_script(login_script)
            if login_result:
                logger.info("Login form submitted, waiting for redirect...")
                await asyncio.sleep(10)  # Wait for login to complete and redirect
                
                # Check if login was successful
                current_url = await browser_client.execute_script("return window.location.href")
                if current_url and self.login_url not in current_url:
                    logger.info(f"Successfully logged in. Current URL: {current_url}")
                    return True
                else:
                    logger.error("Login failed. Still on login page.")
                    return False
            else:
                logger.error("Failed to submit login form")
                return False
        except Exception as e:
            logger.error(f"Error during login: {e}")
            return False
    
    async def extract_properties(self, browser_client) -> Dict[str, Any]:
        """
        Extract property listings from the CBRE DealFlow website.
        
        Returns:
            A dictionary containing the extracted property information.
        """
        # Navigate to the properties page
        logger.info(f"Navigating to {self.properties_url}")
        navigation_success = await browser_client.navigate_to_page(self.properties_url)
        if not navigation_success:
            logger.error(f"Failed to navigate to {self.properties_url}")
            return {"success": False, "error": "Navigation failed"}
        
        # Wait for the page to load
        logger.info("Waiting for page to load...")
        await asyncio.sleep(5)
        
        # Check if authentication is required
        html = await browser_client.get_html()
        if html and ("sign in" in html.lower() or "log in" in html.lower()):
            logger.info("Authentication required. Attempting to log in...")
            if self.has_credentials:
                login_success = await self.login(browser_client)
                if not login_success:
                    logger.error("Failed to log in with provided credentials")
                    return {"success": False, "error": "Authentication failed"}
                
                # Get updated HTML after login
                html = await browser_client.get_html()
            else:
                logger.warning("Authentication required but no credentials provided")
                # Continue with public information only
        
        # Take a screenshot
        logger.info("Taking screenshot")
        screenshot = await browser_client.take_screenshot()
        timestamp = datetime.now()
        
        # Save data to files
        if screenshot:
            await self.storage.save_screenshot(screenshot)
        
        html_path = await self.storage.save_html_content(html)
        
        # Extract page title
        try:
            title = await browser_client.execute_script("document.title")
            logger.info(f"Page title: {title}")
        except Exception as e:
            logger.error(f"Error getting page title: {e}")
            title = "CBRE DealFlow Properties"
        
        # Initialize results
        results = {
            "url": self.properties_url,
            "title": title,
            "analyzed_at": str(timestamp),
            "success": True,
            "properties": []
        }
        
        # Try to extract property data directly from the page's JavaScript data
        try:
            data_extraction_script = """
                try {
                    // Check for any global variables that might contain property data
                    if (window.propertyData) return window.propertyData;
                    if (window.properties) return window.properties;
                    if (window.listings) return window.listings;
                    if (window.siteData && window.siteData.properties) return window.siteData.properties;
                    
                    // Try to find property data in any script tags
                    const scripts = document.querySelectorAll('script');
                    for (const script of scripts) {
                        const content = script.textContent || '';
                        if (content.includes('property') || content.includes('listing')) {
                            // Look for JSON data
                            const jsonMatches = content.match(/\\{[^\\{\\}]*"(property|listing)[^\\{\\}]*\\}/g);
                            if (jsonMatches && jsonMatches.length > 0) {
                                const results = [];
                                for (const match of jsonMatches) {
                                    try {
                                        const data = JSON.parse(match);
                                        if (data && (data.title || data.name)) {
                                            results.push(data);
                                        }
                                    } catch (e) {}
                                }
                                if (results.length > 0) return results;
                            }
                            
                            // Look for array data
                            const arrayMatches = content.match(/\\[[^\\[\\]]*\\{[^\\{\\}]*"(property|listing)[^\\{\\}]*\\}[^\\[\\]]*\\]/g);
                            if (arrayMatches && arrayMatches.length > 0) {
                                for (const match of arrayMatches) {
                                    try {
                                        const data = JSON.parse(match);
                                        if (Array.isArray(data) && data.length > 0) {
                                            return data;
                                        }
                                    } catch (e) {}
                                }
                            }
                        }
                    }
                    
                    // Try to find property data in any data attributes
                    const dataElements = document.querySelectorAll('[data-properties], [data-listings], [data-items]');
                    for (const elem of dataElements) {
                        try {
                            const dataAttr = elem.dataset.properties || elem.dataset.listings || elem.dataset.items;
                            if (dataAttr) {
                                const data = JSON.parse(dataAttr);
                                if (Array.isArray(data) && data.length > 0) {
                                    return data;
                                }
                            }
                        } catch (e) {}
                    }
                    
                    return null;
                } catch (e) {
                    console.error('Error extracting data:', e);
                    return null;
                }
            """
            
            js_data = await browser_client.execute_script(data_extraction_script)
            if js_data and isinstance(js_data, list) and len(js_data) > 0:
                logger.info(f"Extracted {len(js_data)} properties from JavaScript data")
                
                # Process the extracted properties
                properties = []
                for item in js_data:
                    if isinstance(item, dict):
                        # Create property object
                        property_info = {
                            "title": item.get("title", item.get("name", "")).strip(),
                            "description": item.get("description", item.get("summary", "")).strip(),
                            "link": item.get("link", item.get("url", "")).strip(),
                            "location": item.get("location", item.get("address", "")).strip(),
                            "units": item.get("units", "").strip(),
                            "property_type": item.get("propertyType", item.get("type", "Commercial")).strip(),
                            "price": item.get("price", "").strip(),
                            "sq_ft": item.get("sqFt", item.get("squareFeet", "")).strip(),
                            "status": item.get("status", "Available").strip(),
                            "image_url": item.get("imageUrl", item.get("image", "")).strip(),
                            "source": "CBRE DealFlow"
                        }
                        
                        # Only add if we have at least a title
                        if property_info["title"]:
                            properties.append(property_info)
                
                results["properties"] = properties
                logger.info(f"Processed {len(properties)} valid properties from JavaScript data")
        except Exception as e:
            logger.error(f"Error extracting JavaScript data: {e}")
        
        # If we couldn't extract data from JavaScript, try parsing the HTML
        if not results["properties"]:
            # Parse HTML using BeautifulSoup
            try:
                soup = BeautifulSoup(html, 'html.parser')
                
                # Look for property listings
                property_elements = soup.select(".property_area .gridview .item")
                logger.info(f"Found {len(property_elements)} potential property elements")
                
                properties = []
                for element in property_elements:
                    try:
                        # Extract property details
                        property_data = {}
                        
                        # Property type
                        asset_type_elem = element.select_one(".assetBar .asset")
                        if asset_type_elem:
                            property_data["property_type"] = asset_type_elem.text.strip()
                        
                        # Country
                        country_elem = element.select_one(".assetBar .country")
                        if country_elem:
                            country_text = country_elem.text.strip()
                            # Clean up the country text by removing extra characters
                            if "|" in country_text:
                                country_text = country_text.split("|")[-1].strip()
                            property_data["country"] = country_text
                        
                        # Title/Name
                        title_elem = element.select_one(".headline a")
                        if title_elem:
                            property_data["title"] = title_elem.text.strip()
                            property_data["url"] = title_elem.get("href", "")
                            if property_data["url"] and not property_data["url"].startswith("http"):
                                property_data["url"] = self.base_url + property_data["url"]
                        
                        # Description
                        description_elem = element.select_one(".summary p")
                        if description_elem:
                            description_text = description_elem.text.strip()
                            # Clean up the description text by removing extra characters
                            description_text = description_text.replace("\n", " ").replace("\t", "")
                            # Replace the ellipsis character with "..."
                            description_text = description_text.replace("\u2026", "...")
                            property_data["description"] = description_text
                        
                        # Status
                        status_elem = element.select_one(".status")
                        if status_elem:
                            property_data["status"] = status_elem.text.strip()
                        
                        # Image URL
                        img_elem = element.select_one(".img img.img-responsive")
                        if img_elem:
                            property_data["image_url"] = img_elem.get("src", "")
                        
                        # Only add if we have at least a title
                        if property_data.get("title"):
                            properties.append(property_data)
                    except Exception as e:
                        logger.error(f"Error extracting property data: {str(e)}")
                
                logger.info(f"Extracted {len(properties)} properties")
                results["properties"] = properties
            except Exception as e:
                logger.error(f"Error parsing HTML: {e}")
        
        # If we still don't have any properties and we're not authenticated, add a note about authentication
        if not results["properties"]:
            if not self.has_credentials:
                logger.warning("No properties extracted. Authentication may be required.")
                results["error"] = "Authentication required to access property listings"
            else:
                logger.warning("No properties extracted even with authentication")
        
        # Save the extracted data
        if results["properties"]:
            await self.storage.save_extracted_data(results["properties"])
            
            # Save to database if enabled
            try:
                logger.info("Saving properties to database")
                await self.storage.save_to_database(results["properties"])
                logger.info("Successfully saved properties to database")
            except Exception as e:
                logger.error(f"Error saving to database: {e}")
        else:
            logger.warning("No properties extracted")
        
        return results


async def main():
    """
    Main function to run the scraper directly.
    """
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger(__name__)
    
    logger.info("Starting CBRE DealFlow scraper")
    
    # Initialize the browser client
    browser_client = MCPClient(base_url="http://localhost:3001")
    
    try:
        # Initialize the storage
        storage = ScraperDataStorage(broker_name="cbredealflow", save_to_db=True)
        
        # Initialize and run the scraper
        scraper = CBREDealFlowScraper()
        scraper.client = browser_client
        scraper.storage = storage
        
        # Extract properties
        result = await scraper.extract_properties(browser_client)
        
        # Log the results
        if result["success"]:
            logger.info(f"Successfully extracted {len(result['properties'])} properties")
            for i, prop in enumerate(result["properties"], 1):
                logger.info(f"Property {i}: {prop.get('title', 'No Title')} - {prop.get('location', 'No Location')}")
        else:
            logger.error(f"Failed to extract properties: {result.get('error', 'Unknown error')}")
        
        return result
    
    finally:
        # Log completion
        logger.info("CBRE DealFlow scraper completed")


if __name__ == "__main__":
    asyncio.run(main())
