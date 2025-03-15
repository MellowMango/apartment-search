#!/usr/bin/env python3
"""
Script to run the CBRE DealFlow scraper.
"""

import os
import sys
import logging
import json
import asyncio
from datetime import datetime
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from backend.scrapers.core.mcp_client import MCPClient
from backend.scrapers.core.storage import ScraperDataStorage

# Add the project directory to the path so we can import our modules
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

class CBREDealFlowScraper:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.base_url = "https://www.cbredealflow.com"
        self.username = os.environ.get("CBREDEALFLOW_USERNAME", "")
        self.password = os.environ.get("CBREDEALFLOW_PASSWORD", "")
        self.storage = ScraperDataStorage("cbredealflow", save_to_db=True)
        
    async def login(self, browser_client):
        """Attempt to log in to CBRE DealFlow if credentials are provided"""
        if not self.username or not self.password:
            self.logger.warning("No credentials found for CBRE DealFlow. Will only scrape public data.")
            return False
        
        try:
            self.logger.info("Attempting to log in to CBRE DealFlow...")
            success = await browser_client.navigate_to_page(f"{self.base_url}/partner/portal/Login/Login.aspx")
            if not success:
                self.logger.error("Failed to navigate to login page")
                return False
            
            # Fill in username and password using JavaScript
            await browser_client.execute_script(f"""
                document.querySelector('#txtUserName').value = '{self.username}';
                document.querySelector('#txtPassword').value = '{self.password}';
                document.querySelector('#btnLogin').click();
            """)
            
            # Wait for navigation to complete
            await asyncio.sleep(5)
            
            # Check if login was successful by checking the URL
            current_url = await browser_client.execute_script("return window.location.href")
            if current_url and "Login" not in current_url:
                self.logger.info("Successfully logged in to CBRE DealFlow")
                return True
            else:
                self.logger.error("Failed to log in to CBRE DealFlow")
                return False
        except Exception as e:
            self.logger.error(f"Error during login: {str(e)}")
            return False
    
    async def extract_properties(self, browser_client):
        """Extract property listings from CBRE DealFlow"""
        self.logger.info("Navigating to CBRE DealFlow properties page...")
        success = await browser_client.navigate_to_page(self.base_url)
        if not success:
            self.logger.error("Failed to navigate to CBRE DealFlow homepage")
            return []
        
        # Save the HTML content
        html_content = await browser_client.get_html()
        await self.storage.save_html_content(html_content)
        
        # Parse the HTML with BeautifulSoup
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Look for property listings
        property_elements = soup.select(".property_area .gridview .item")
        self.logger.info(f"Found {len(property_elements)} potential property elements")
        
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
                self.logger.error(f"Error extracting property data: {str(e)}")
        
        self.logger.info(f"Extracted {len(properties)} properties")
        return properties
    
    async def save_properties(self, properties):
        """Save extracted properties to storage"""
        if not properties:
            self.logger.warning("No properties to save")
            return
        
        # Save to files
        await self.storage.save_extracted_data(properties)
        self.logger.info(f"Saved {len(properties)} properties to storage")
        
        # Save to database
        try:
            self.logger.info("Saving properties to database...")
            await self.storage.save_to_database(properties)
            self.logger.info(f"Successfully saved {len(properties)} properties to database")
        except Exception as e:
            self.logger.error(f"Error saving to database: {str(e)}")
    
    async def run(self):
        """Run the CBRE DealFlow scraper"""
        browser_client = None
        try:
            self.logger.info("Starting CBRE DealFlow scraper...")
            browser_client = MCPClient(base_url="http://localhost:3001")
            
            # Attempt to login if credentials are provided
            logged_in = await self.login(browser_client)
            
            # Extract properties
            properties = await self.extract_properties(browser_client)
            
            # Save properties
            await self.save_properties(properties)
            
            return properties
        except Exception as e:
            self.logger.error(f"Error running CBRE DealFlow scraper: {str(e)}")
            return []
        finally:
            self.logger.info("CBRE DealFlow scraper completed")

async def main():
    """Main function to run the scraper"""
    try:
        scraper = CBREDealFlowScraper()
        properties = await scraper.run()
        print(f"Extracted {len(properties)} properties")
    except Exception as e:
        logger.error(f"Error in main function: {str(e)}")
    finally:
        logger.info("Script completed")

if __name__ == "__main__":
    asyncio.run(main()) 