#!/usr/bin/env python3
"""
Enhanced Broker Website Scraping Test Script

This version attempts to be as website-agnostic as possible by:
1. Trying multiple extraction strategies (listing cards, property links, and content analysis)
2. Using adaptive learning to cache successful strategies per domain
3. Simulating user interactions (scrolling and clicking "load more")
4. Adding improved error handling and wait times
"""

import os
import sys
import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
import importlib.util
import types
from unittest.mock import patch, MagicMock

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# Add the backend directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# --- Mock settings and modules ---
mock_settings_module = types.ModuleType('backend.app.core.config')
mock_settings_module.__file__ = 'mock_config.py'

class Settings:
    """Mock settings class for testing."""
    MCP_SERVER_TYPE = "playwright"  # Using Playwright for testing
    MCP_PLAYWRIGHT_URL = "http://localhost:3001"
    MCP_PUPPETEER_URL = "http://localhost:3002"
    FIRECRAWL_API_URL = "https://api.firecrawl.dev"
    FIRECRAWL_API_KEY = os.environ.get("FIRECRAWL_API_KEY", "mock_api_key")
    MCP_MAX_CONCURRENT_SESSIONS = 1
    MCP_REQUEST_TIMEOUT = 60
    SCRAPER_USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36"
    MCP_ENABLE_LLM_GUIDANCE = False
    MCP_USE_LLM_GUIDANCE = False
    MCP_LLM_PROVIDER = "openai"
    MCP_LLM_MODEL = "gpt-3.5-turbo"
    SUPABASE_URL = "https://mock.supabase.co"
    SUPABASE_KEY = "mock_supabase_key"
    CORS_ORIGINS = ["http://localhost:3000"]
    PLAYWRIGHT_HEADLESS = True
    SCRAPER_TIMEOUT = 60

mock_settings_module.settings = Settings()
sys.modules['backend.app.core.config'] = mock_settings_module

mock_supabase_module = types.ModuleType('backend.app.db.supabase')
mock_supabase_module.__file__ = 'mock_supabase.py'
def get_supabase_client():
    """Mock function to get a Supabase client."""
    return MagicMock()
mock_supabase_module.get_supabase_client = get_supabase_client
sys.modules['backend.app.db.supabase'] = mock_supabase_module

mock_data_models_module = types.ModuleType('backend.app.models.data_models')
mock_data_models_module.__file__ = 'mock_data_models.py'
class PropertyDict(dict):
    """Mock PropertyDict class for testing."""
    pass
mock_data_models_module.PropertyDict = PropertyDict
sys.modules['backend.app.models.data_models'] = mock_data_models_module

# Now import the actual MCP client and scraper
from backend.app.services.mcp_client import mcp_client
from backend.app.services.mcp_scraper import mcp_scraper

# --- Broker website definitions ---
BROKER_WEBSITES = [
    {
        "name": "ACR Multifamily",
        "url": "https://www.acrmultifamily.com/properties",
        "brokerage_id": "acr-multifamily",
        "description": "ACR Multifamily specializes in multifamily property sales."
    },
    {
        "name": "Multifamily Group",
        "url": "https://multifamilygrp.com/listings/",
        "brokerage_id": "multifamily-group",
        "description": "The Multifamily Group is a commercial real estate brokerage firm specializing in the sale of apartment communities."
    },
    {
        "name": "Marcus & Millichap",
        "url": "https://www.marcusmillichap.com/properties#f-propertysubtypeid_Apartments=Mixed-Use,Multifamily,Multifamily%20HUD,Multifamily%20Tax%20Credit,Multifamily%20Vacant-User,Student%20Housing&f-propertytype=Apartments&pageNumber=1&stb=orderdate,DESC",
        "brokerage_id": "marcus-millichap",
        "description": "Marcus & Millichap specializes in commercial real estate investment sales, financing, research and advisory services."
    },
    {
        "name": "Transwestern",
        "url": "https://transwestern.com/properties",
        "brokerage_id": "transwestern",
        "description": "Transwestern is a diversified real estate operating company."
    },
    {
        "name": "Walker & Dunlop",
        "url": "https://properties.walkerdunlop.com/",
        "brokerage_id": "walker-dunlop",
        "description": "Walker & Dunlop is one of the largest commercial real estate finance companies in the United States."
    }
]

# --- JavaScript Extraction Strategies ---
PROPERTY_SELECTORS = {
    "listing_cards": """
        // Find all property listing cards on the page
        function findListingCards() {
            const cardSelectors = [
                'div[class*="property-card"]',
                'div[class*="listing-card"]',
                'div[class*="property-item"]',
                'div[class*="property-listing"]',
                'article[class*="property"]',
                '.property-card',
                '.listing-card',
                '.property-item',
                '.property-listing',
                '.property',
                'div[id*="property-"]',
                'div[data-property-id]',
                'div[class*="card"][class*="property"]',
                'div[class*="card"][class*="listing"]'
            ];
            for (const selector of cardSelectors) {
                const elements = document.querySelectorAll(selector);
                if (elements && elements.length > 0) {
                    return Array.from(elements);
                }
            }
            // Fallback: heuristic based on content patterns
            const allDivs = document.querySelectorAll('div');
            const potentialCards = Array.from(allDivs).filter(div => {
                const text = div.textContent.toLowerCase();
                const hasPrice = text.includes('price') || text.match(/\\$[\\d,]+/) !== null;
                const hasUnits = text.includes('unit') || text.includes('apartment');
                const hasLocation = text.includes('location') || text.includes('address');
                return (hasPrice || hasUnits || hasLocation) &&
                       div.querySelectorAll('*').length > 5 &&
                       div.querySelectorAll('img').length > 0;
            });
            return potentialCards;
        }
        function extractPropertyData(cards) {
            return cards.map(card => {
                const name = findText(card, ['h1', 'h2', 'h3', 'h4', '.title', '[class*="title"]', '[class*="name"]']);
                const address = findText(card, ['.address', '[class*="address"]', '[class*="location"]', 'p:contains("Address")']);
                const price = findPrice(card);
                const units = findNumber(card, ['unit', 'units', 'apartment']);
                const sqft = findNumber(card, ['sq ft', 'sqft', 'square feet', 'square foot']);
                const link = card.querySelector('a[href*="property"], a[href*="listing"], a[href*="detail"]');
                const detailUrl = link ? link.href : null;
                return {
                    name,
                    address,
                    price,
                    units,
                    square_feet: sqft,
                    detail_url: detailUrl
                };
            });
        }
        function findText(element, selectors) {
            for (const selector of selectors) {
                const el = element.querySelector(selector);
                if (el && el.textContent.trim()) {
                    return el.textContent.trim();
                }
            }
            return null;
        }
        function findPrice(element) {
            const text = element.textContent;
            const priceMatch = text.match(/\\$[\\d,]+(?:\\.\\d+)?(?:\\s*(?:million|M))?/);
            return priceMatch ? priceMatch[0] : null;
        }
        function findNumber(element, keywords) {
            const text = element.textContent.toLowerCase();
            for (const keyword of keywords) {
                const pattern = new RegExp(`(\\d+)\\s*${keyword}|${keyword}[^\\d]*(\\d+)`, 'i');
                const match = text.match(pattern);
                if (match) {
                    return match[1] || match[2];
                }
            }
            return null;
        }
        const cards = findListingCards();
        return extractPropertyData(cards);
    """,

    "property_links": """
        // Find all links to property detail pages
        function findPropertyLinks() {
            const linkSelectors = [
                'a[href*="property"]',
                'a[href*="listing"]',
                'a[href*="detail"]',
                'a[href*="for-sale"]',
                'a[class*="property"]',
                'a[class*="listing"]',
                'a[data-property-id]'
            ];
            const allLinks = [];
            for (const selector of linkSelectors) {
                const links = document.querySelectorAll(selector);
                if (links && links.length > 0) {
                    allLinks.push(...Array.from(links).map(link => link.href));
                }
            }
            return [...new Set(allLinks)].filter(url => {
                return url.includes('property') || 
                       url.includes('listing') || 
                       url.includes('detail') || 
                       url.includes('for-sale');
            });
        }
        return findPropertyLinks();
    """,

    "content_analysis": """
        // Use content analysis heuristics to extract property data
        function contentAnalysisExtraction() {
            const elements = document.querySelectorAll('div, article, section');
            const candidates = [];
            for (const el of elements) {
                const text = el.innerText.toLowerCase();
                if ((text.includes('price') || text.match(/\\$[\\d,]+/)) &&
                    (text.includes('unit') || text.includes('apartment')) &&
                    (text.includes('address') || text.includes('location'))) {
                    candidates.push(el);
                }
            }
            return candidates.map(card => {
                const name = card.querySelector('h1, h2, h3, h4, .title, [class*="name"]') ? card.querySelector('h1, h2, h3, h4, .title, [class*="name"]').innerText.trim() : null;
                const address = card.querySelector('.address, [class*="location"], [class*="address"]') ? card.querySelector('.address, [class*="location"], [class*="address"]').innerText.trim() : null;
                const priceMatch = card.innerText.match(/\\$[\\d,]+(?:\\.\\d+)?/);
                const price = priceMatch ? priceMatch[0] : null;
                const link = card.querySelector('a[href]') ? card.querySelector('a[href]').href : null;
                return { name, address, price, detail_url: link };
            });
        }
        return contentAnalysisExtraction();
    """
}

# --- Adaptive Learning: Cache for successful extraction strategies per domain ---
successful_strategies: Dict[str, str] = {}

# --- Simulate User Interactions ---
async def simulate_interaction(session_id: str):
    """Simulate scrolling and click 'load more' to prompt dynamic loading."""
    try:
        logger.info("Simulating user interactions: scrolling and attempting 'load more'.")
        await mcp_client.execute_script(session_id, """
            window.scrollTo(0, document.body.scrollHeight);
            let loadMore = document.querySelector('button.load-more, a.load-more');
            if(loadMore) { loadMore.click(); }
        """)
        await asyncio.sleep(3)
    except Exception as e:
        logger.warning("simulate_interaction error: " + str(e))

# --- Enhanced Property Listing Extraction ---
async def find_property_listings(session_id: str, website: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Find property listings on a broker website using multiple strategies.
    Uses adaptive learning to try the previously successful strategy first.
    """
    domain = website.get("brokerage_id", "default")
    logger.info(f"Finding property listings on {website['name']} (Domain: {domain})")
    
    try:
        # Navigate to the website and simulate interactions
        await mcp_client.navigate(session_id, website["url"])
        logger.info(f"Navigated to {website['url']}")
        await asyncio.sleep(3)
        await simulate_interaction(session_id)
        
        # Determine the order of strategies based on past success
        let_strategies = ["listing_cards", "property_links", "content_analysis"]
        if domain in successful_strategies:
            preferred = successful_strategies[domain]
            strategies = [preferred] + [s for s in let_strategies if s != preferred]
        else:
            strategies = let_strategies

        # Try each extraction strategy in sequence
        for strategy in strategies:
            logger.info(f"Trying extraction strategy: {strategy} for {website['name']}")
            try:
                property_data = await mcp_client.execute_script(session_id, PROPERTY_SELECTORS[strategy])
            except Exception as ex:
                logger.error(f"Error running strategy {strategy}: {str(ex)}")
                property_data = None

            if property_data and isinstance(property_data, list) and len(property_data) > 0:
                logger.info(f"Strategy '{strategy}' found {len(property_data)} listings on {website['name']}")
                successful_strategies[domain] = strategy  # Cache the successful strategy
                # Annotate properties with domain info
                for prop in property_data:
                    if isinstance(prop, dict):
                        prop["brokerage_id"] = website.get("brokerage_id")
                        prop["source_url"] = website.get("url")
                return property_data

        logger.warning(f"No property listings found on {website['name']} using any strategy.")
        return []
                
    except Exception as e:
        logger.error(f"Error finding property listings: {str(e)}")
        return []

# --- Detailed Property Data Extraction ---
async def extract_property_details(session_id: str, property_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Extract detailed property data from a property detail page.
    Falls back to already available data if no detail URL is provided.
    """
    if not property_data.get("detail_url"):
        logger.warning("No detail URL provided for property; skipping detailed extraction.")
        return property_data
    
    detail_url = property_data["detail_url"]
    logger.info(f"Extracting property details from {detail_url}")
    
    try:
        await mcp_client.navigate(session_id, detail_url)
        logger.info(f"Navigated to {detail_url}")
        await asyncio.sleep(3)
        
        # Extraction using multiple simple scripts
        name = await mcp_client.execute_script(
            session_id,
            """
            const selectors = ['h1', 'h2', '.property-title', '[class*="property-title"]', '[class*="listing-title"]'];
            for (const selector of selectors) {
                const el = document.querySelector(selector);
                if (el && el.textContent.trim()) return el.textContent.trim();
            }
            return null;
            """
        )
        address = await mcp_client.execute_script(
            session_id,
            """
            const selectors = ['.address', '[class*="address"]', '[class*="location"]', 'p:contains("Address")'];
            for (const selector of selectors) {
                const el = document.querySelector(selector);
                if (el && el.textContent.trim()) return el.textContent.trim();
            }
            return null;
            """
        )
        price = await mcp_client.execute_script(
            session_id,
            """
            const text = document.body.textContent;
            const priceMatch = text.match(/\\$[\\d,]+(?:\\.\\d+)?(?:\\s*(?:million|M))?/);
            return priceMatch ? priceMatch[0] : null;
            """
        )
        units = await mcp_client.execute_script(
            session_id,
            """
            const text = document.body.textContent.toLowerCase();
            const unitPatterns = [
                /(\\d+)\\s*units/i,
                /units[^\\d]*(\\d+)/i,
                /(\\d+)\\s*apartments/i,
                /apartments[^\\d]*(\\d+)/i
            ];
            for (const pattern of unitPatterns) {
                const match = text.match(pattern);
                if (match) return match[1] || match[2];
            }
            return null;
            """
        )
        square_feet = await mcp_client.execute_script(
            session_id,
            """
            const text = document.body.textContent.toLowerCase();
            const sqftPatterns = [
                /(\\d+(?:,\\d+)?)\\s*(?:sq\\.?\\s*ft\\.?|square\\s*feet)/i,
                /(?:sq\\.?\\s*ft\\.?|square\\s*feet)[^\\d]*(\\d+(?:,\\d+)?)/i
            ];
            for (const pattern of sqftPatterns) {
                const match = text.match(pattern);
                if (match) return match[1] || match[2];
            }
            return null;
            """
        )
        description = await mcp_client.execute_script(
            session_id,
            """
            const selectors = [
                '.description', 
                '[class*="description"]', 
                '[class*="property-description"]',
                '[class*="listing-description"]',
                'p.lead',
                'div[class*="content"] > p'
            ];
            for (const selector of selectors) {
                const el = document.querySelector(selector);
                if (el && el.textContent.trim()) return el.textContent.trim();
            }
            const paragraphs = document.querySelectorAll('p');
            for (const p of paragraphs) {
                if (p.textContent.trim().length > 100) return p.textContent.trim();
            }
            return null;
            """
        )
        images = await mcp_client.execute_script(
            session_id,
            """
            const images = document.querySelectorAll('img[src*="property"], img[class*="property"], img[class*="listing"]');
            return Array.from(images).map(img => img.src).filter(src => src && !src.includes('logo') && !src.includes('icon'));
            """
        )
        screenshot = await mcp_client.take_screenshot(session_id)
        
        detailed_property = {
            **property_data,
            "name": name or property_data.get("name"),
            "address": address or property_data.get("address"),
            "price": price or property_data.get("price"),
            "units": units or property_data.get("units"),
            "square_feet": square_feet or property_data.get("square_feet"),
            "description": description,
            "images": images if isinstance(images, list) else [],
            "listing_website": detail_url,
            "screenshot": screenshot
        }
        
        return detailed_property
            
    except Exception as e:
        logger.error(f"Error extracting property details from {detail_url}: {str(e)}")
        return property_data

# --- Testing a Broker Website ---
async def test_broker_website(website: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Test scraping a broker website by:
    1. Creating a new browser session
    2. Finding property listings using adaptive strategies
    3. Extracting detailed property data for a subset of listings
    """
    logger.info(f"Testing scraping on {website['name']}")
    session_id = None
    properties = []
    
    try:
        session_id = await mcp_client.create_session()
        logger.info(f"Created MCP session: {session_id}")
        
        property_listings = await find_property_listings(session_id, website)
        logger.info(f"Found {len(property_listings)} property listings on {website['name']}")
        
        # Limit to a few properties for testing
        for property_data in property_listings[:3]:
            detailed_property = await extract_property_details(session_id, property_data)
            if detailed_property:
                properties.append(detailed_property)
                
        logger.info(f"Extracted {len(properties)} detailed properties from {website['name']}")
        return properties
        
    except Exception as e:
        logger.error(f"Error testing broker website {website['name']}: {str(e)}")
        return []
        
    finally:
        if session_id:
            try:
                await mcp_client.close_session(session_id)
                logger.info(f"Closed MCP session: {session_id}")
            except Exception as e:
                logger.error(f"Error closing session {session_id}: {str(e)}")

# --- Main Function ---
async def main():
    logger.info("=== Enhanced Broker Website Scraping Test ===")
    all_properties = []
    
    for website in BROKER_WEBSITES:
        properties = await test_broker_website(website)
        all_properties.extend(properties)
        
        if properties:
            output_dir = "scraped_properties"
            os.makedirs(output_dir, exist_ok=True)
            output_file = f"{output_dir}/properties_{website['name'].lower().replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            
            # Prepare data for JSON serialization
            serializable_properties = []
            for prop in properties:
                prop_copy = prop.copy()
                if "screenshot" in prop_copy:
                    prop_copy["screenshot"] = f"[Screenshot data exists - {len(prop_copy['screenshot'])} bytes]"
                serializable_properties.append(prop_copy)
            
            with open(output_file, "w") as f:
                json.dump(serializable_properties, f, indent=2)
            logger.info(f"Saved {len(properties)} properties to {output_file}")
    
    logger.info("=== Summary ===")
    logger.info(f"Total properties extracted: {len(all_properties)}")
    for website in BROKER_WEBSITES:
        website_properties = [p for p in all_properties if p.get("brokerage_id") == website.get("brokerage_id")]
        logger.info(f"{website['name']}: {len(website_properties)} properties")
    
    return 0

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)