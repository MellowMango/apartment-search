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
import signal

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
        "name": "Example",
        "url": "https://example.com",
        "brokerage_id": "example",
        "description": "A simple example website for testing."
    },
    {
        "name": "Apartments.com",
        "url": "https://www.apartments.com/austin-tx/",
        "brokerage_id": "apartments-com",
        "description": "Apartments.com is a leading online apartment listing website."
    },
    {
        "name": "Zillow",
        "url": "https://www.zillow.com/austin-tx/apartments/",
        "brokerage_id": "zillow",
        "description": "Zillow is a real estate and rental marketplace."
    },
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
    "debug_info": """
        // Get debug information about the page
        function getDebugInfo() {
            return {
                url: window.location.href,
                title: document.title,
                readyState: document.readyState,
                bodyContent: document.body ? document.body.innerText.substring(0, 500) + '...' : 'No body',
                htmlContent: document.documentElement ? document.documentElement.outerHTML.substring(0, 500) + '...' : 'No HTML',
                links: Array.from(document.querySelectorAll('a')).map(a => a.href).slice(0, 10),
                images: Array.from(document.querySelectorAll('img')).map(img => img.src).slice(0, 10),
                scripts: Array.from(document.querySelectorAll('script')).map(s => s.src).filter(Boolean).slice(0, 10)
            };
        }
        return getDebugInfo();
    """,

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
                'div[class*="card"][class*="listing"]',
                // Add more generic selectors
                '.card',
                '.item',
                '.listing',
                'article',
                '.col-md-4',  // Common Bootstrap column that might contain cards
                '.col-lg-4',
                '.col-sm-6'
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
                const link = card.querySelector('a[href*="property"], a[href*="listing"], a[href*="detail"]') || 
                             card.querySelector('a'); // Fallback to any link
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
                'a[data-property-id]',
                // Add more generic selectors
                'a.btn',
                'a.button',
                'a.view',
                'a.more',
                'a.details',
                'a[class*="btn"]',
                'a[class*="view"]'
            ];
            const allLinks = [];
            
            // Try each selector
            for (const selector of linkSelectors) {
                const links = document.querySelectorAll(selector);
                if (links && links.length > 0) {
                    allLinks.push(...Array.from(links).map(link => link.href));
                }
            }
            
            // If no specific links found, get all links and filter by likely property URLs
            if (allLinks.length === 0) {
                const allPageLinks = document.querySelectorAll('a[href]');
                allLinks.push(...Array.from(allPageLinks)
                    .map(link => link.href)
                    .filter(url => {
                        const urlLower = url.toLowerCase();
                        return urlLower.includes('property') || 
                               urlLower.includes('listing') || 
                               urlLower.includes('detail') || 
                               urlLower.includes('for-sale') ||
                               urlLower.includes('apartment') ||
                               urlLower.includes('multifamily') ||
                               urlLower.match(/\\d+-\\d+/) !== null; // URLs with numbers like "123-456" often property IDs
                    }));
            }
            
            return [...new Set(allLinks)];
        }
        
        return findPropertyLinks();
    """,

    "content_analysis": """
        // Use content analysis heuristics to extract property data
        function contentAnalysisExtraction() {
            // Look for elements that might contain property data
            const elements = document.querySelectorAll('div, article, section, li, .card, .item, .listing');
            const candidates = [];
            
            // First pass: look for elements with property-related content
            for (const el of elements) {
                const text = el.innerText.toLowerCase();
                // Check for property-related keywords
                if ((text.includes('price') || text.match(/\\$[\\d,]+/)) ||
                    (text.includes('unit') || text.includes('apartment')) ||
                    (text.includes('address') || text.includes('location')) ||
                    (text.includes('sqft') || text.includes('square feet')) ||
                    (text.includes('bed') && text.includes('bath'))) {
                    candidates.push(el);
                }
            }
            
            // If no candidates found, try DOM structure analysis
            if (candidates.length === 0) {
                // Look for grid layouts which often contain property listings
                const gridContainers = document.querySelectorAll('.row, .grid, .container, [class*="grid"], [class*="list"]');
                for (const container of gridContainers) {
                    // Find child elements that look like they might be property cards
                    const childElements = container.children;
                    if (childElements.length >= 2 && 
                        Array.from(childElements).every(child => child.tagName === childElements[0].tagName)) {
                        // If container has multiple children of the same type, they might be property cards
                        candidates.push(...Array.from(childElements));
                    }
                }
            }
            
            // Extract data from candidates
            return candidates.map(card => {
                // Try to find property name
                const name = card.querySelector('h1, h2, h3, h4, .title, [class*="name"]') ? 
                    card.querySelector('h1, h2, h3, h4, .title, [class*="name"]').innerText.trim() : null;
                
                // Try to find address
                const address = card.querySelector('.address, [class*="location"], [class*="address"]') ? 
                    card.querySelector('.address, [class*="location"], [class*="address"]').innerText.trim() : null;
                
                // Try to find price
                const priceMatch = card.innerText.match(/\\$[\\d,]+(?:\\.\\d+)?/);
                const price = priceMatch ? priceMatch[0] : null;
                
                // Try to find link
                const link = card.querySelector('a[href]') ? card.querySelector('a[href]').href : null;
                
                // Try to find units
                const unitMatch = card.innerText.toLowerCase().match(/(\\d+)\\s*units|units[^\\d]*(\\d+)/i);
                const units = unitMatch ? (unitMatch[1] || unitMatch[2]) : null;
                
                return { 
                    name, 
                    address, 
                    price, 
                    units,
                    detail_url: link 
                };
            });
        }
        return contentAnalysisExtraction();
    """,
    
    "dom_structure_analysis": """
        // Analyze DOM structure to find property listings
        function analyzeDOM() {
            // Find all elements that might be containers for property listings
            const containers = [];
            
            // Look for grid layouts
            const gridLayouts = document.querySelectorAll('.row, .grid, .container, [class*="grid"], [class*="list"]');
            containers.push(...Array.from(gridLayouts));
            
            // Look for elements with multiple similar children
            const allElements = document.querySelectorAll('div, ul, section');
            for (const el of allElements) {
                const children = el.children;
                if (children.length >= 2) {
                    // Check if children have similar structure
                    const firstChild = children[0];
                    const similarChildren = Array.from(children).filter(child => {
                        return child.tagName === firstChild.tagName && 
                               Math.abs(child.querySelectorAll('*').length - firstChild.querySelectorAll('*').length) < 5;
                    });
                    
                    if (similarChildren.length >= 2) {
                        containers.push(el);
                    }
                }
            }
            
            // For each container, extract its children as potential property cards
            const potentialCards = [];
            for (const container of containers) {
                const children = container.children;
                if (children.length >= 2) {
                    potentialCards.push(...Array.from(children));
                }
            }
            
            // Extract data from potential cards
            return potentialCards.map(card => {
                // Try to find property name (any heading or element with title-like class)
                const name = card.querySelector('h1, h2, h3, h4, .title, [class*="title"], [class*="name"]') ? 
                    card.querySelector('h1, h2, h3, h4, .title, [class*="title"], [class*="name"]').innerText.trim() : null;
                
                // Try to find address
                const address = card.querySelector('.address, [class*="location"], [class*="address"]') ? 
                    card.querySelector('.address, [class*="location"], [class*="address"]').innerText.trim() : null;
                
                // Try to find price
                const priceMatch = card.innerText.match(/\\$[\\d,]+(?:\\.\\d+)?/);
                const price = priceMatch ? priceMatch[0] : null;
                
                // Try to find link
                const link = card.querySelector('a[href]') ? card.querySelector('a[href]').href : null;
                
                return { 
                    name, 
                    address, 
                    price, 
                    detail_url: link 
                };
            }).filter(item => item.name || item.address || item.price || item.detail_url);
        }
        return analyzeDOM();
    """
}

# --- Adaptive Learning: Cache for successful extraction strategies per domain ---
successful_strategies: Dict[str, str] = {}

# --- Simulate User Interactions ---
async def simulate_interaction(session_id: str):
    """Simulate scrolling and click 'load more' to prompt dynamic loading."""
    try:
        logger.info("Simulating user interactions: scrolling and attempting 'load more'.")
        
        # Scroll down multiple times to trigger lazy loading
        for i in range(3):
            await mcp_client.execute_script(session_id, "window.scrollTo(0, document.body.scrollHeight);")
            await asyncio.sleep(1)
        
        # Try to click various "load more" buttons
        await mcp_client.execute_script(session_id, """
            // Try to find and click load more buttons
            const loadMoreSelectors = [
                'button.load-more', 'a.load-more', 
                '[class*="load-more"]', '[class*="loadMore"]',
                'button.more', 'a.more', 
                'button.view-more', 'a.view-more',
                '.pagination a', '.pager a',
                'button:contains("Load")', 'a:contains("Load")',
                'button:contains("More")', 'a:contains("More")',
                'button:contains("View")', 'a:contains("View")'
            ];
            
            for (const selector of loadMoreSelectors) {
                const loadMore = document.querySelector(selector);
                if (loadMore) { 
                    loadMore.click();
                    console.log("Clicked load more button:", selector);
                    break;
                }
            }
        """)
        
        # Wait for content to load
        await asyncio.sleep(3)
    except Exception as e:
        logger.warning("simulate_interaction error: " + str(e))

# --- Wait for Dynamic Content ---
async def wait_for_dynamic_content(session_id: str):
    """Wait for dynamic content to load on the page."""
    try:
        logger.info("Waiting for dynamic content to load...")
        
        # Wait for network activity to settle
        await mcp_client.execute_script(session_id, """
            return new Promise(resolve => {
                // Check if page has finished loading
                if (document.readyState === 'complete') {
                    resolve();
                    return;
                }
                
                // Wait for page to finish loading
                window.addEventListener('load', resolve);
                
                // Fallback: resolve after a timeout
                setTimeout(resolve, 5000);
            });
        """)
        
        # Wait a bit more for any JavaScript frameworks to render content
        await asyncio.sleep(2)
    except Exception as e:
        logger.warning("wait_for_dynamic_content error: " + str(e))

# --- Enhanced Property Listing Extraction ---
async def find_property_listings(session_id: str, website: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Find property listings on a broker website using multiple strategies.
    Uses adaptive learning to try the previously successful strategy first.
    """
    domain = website.get("brokerage_id", "default")
    logger.info(f"Finding property listings on {website['name']} (Domain: {domain})")
    
    try:
        # Set a user agent to look more like a real browser
        await mcp_client.execute_script(session_id, """
            Object.defineProperty(navigator, 'userAgent', {
                get: function () {
                    return 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36';
                }
            });
        """)
        
        # Navigate to the website
        await mcp_client.navigate(session_id, website["url"])
        logger.info(f"Navigated to {website['url']}")
        
        # Get debug information about the page
        debug_info = await mcp_client.execute_script(session_id, PROPERTY_SELECTORS["debug_info"])
        logger.info(f"Debug info for {website['name']}:")
        logger.info(f"  URL: {debug_info.get('url')}")
        logger.info(f"  Title: {debug_info.get('title')}")
        logger.info(f"  Ready state: {debug_info.get('readyState')}")
        logger.info(f"  Links: {debug_info.get('links')}")
        
        # Wait for dynamic content to load
        await wait_for_dynamic_content(session_id)
        
        # Simulate user interactions
        await simulate_interaction(session_id)
        
        # Determine the order of strategies based on past success
        strategies_list = ["listing_cards", "property_links", "content_analysis", "dom_structure_analysis"]
        if domain in successful_strategies:
            preferred = successful_strategies[domain]
            strategies = [preferred] + [s for s in strategies_list if s != preferred]
        else:
            strategies = strategies_list

        # Try each extraction strategy in sequence
        for strategy in strategies:
            logger.info(f"Trying extraction strategy: {strategy} for {website['name']}")
            try:
                property_data = await mcp_client.execute_script(session_id, PROPERTY_SELECTORS[strategy])
                
                # Debug: Take a screenshot to see what the page looks like
                if strategy == strategies[0]:  # Only for the first strategy
                    screenshot = await mcp_client.take_screenshot(session_id)
                    debug_dir = "debug_screenshots"
                    os.makedirs(debug_dir, exist_ok=True)
                    debug_file = f"{debug_dir}/{website['name'].lower().replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                    with open(debug_file, "wb") as f:
                        f.write(screenshot)
                    logger.info(f"Saved debug screenshot to {debug_file} (size: {len(screenshot)} bytes)")
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
                        prop["extraction_strategy"] = strategy
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
        
        # Limit to just 1 property for testing to keep compute costs low
        for property_data in property_listings[:1]:  # Only test the first property
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
    
    # Set a timeout for the entire script (5 minutes)
    def timeout_handler(signum, frame):
        logger.warning("Script execution timed out after 5 minutes")
        sys.exit(1)
    
    # Register the timeout handler
    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(300)  # 5 minutes timeout
    
    all_properties = []
    
    # Limit testing to just 2 broker websites to keep compute costs low during testing
    test_websites = BROKER_WEBSITES[:2]  # Only test the first two websites
    logger.info(f"Testing limited to {len(test_websites)} websites to keep compute costs low")
    
    for website in test_websites:
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
    for website in test_websites:
        website_properties = [p for p in all_properties if p.get("brokerage_id") == website.get("brokerage_id")]
        logger.info(f"{website['name']}: {len(website_properties)} properties")
    
    return 0

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code) 