# Broker Scrapers Pattern Guide

This guide documents the common pattern used across all broker scrapers in the Acquire Apartments project. Follow this guide when creating, testing, and maintaining broker-specific scrapers.

## Directory Structure Pattern

Each broker scraper should maintain the following structure:

```
brokers/
└── <broker_name>/
    ├── __init__.py             # Package initialization
    ├── scraper.py              # Main scraper implementation
    ├── test_<broker>_scraper.py # Tests for scraper
    ├── test_db_storage.py      # Tests for database storage
    └── README.md               # Documentation specific to this scraper
```

And at the project root:

```
backend/
├── run_<broker>_scraper.py     # Runner script for this specific broker
└── [...]                       # Other project files
```

## Scraper Class Implementation Pattern

All broker scrapers should follow this implementation pattern:

```python
from backend.scrapers.core.mcp_client import MCPClient
from backend.scrapers.core.storage import ScraperDataStorage
from backend.scrapers.core.property import Property

class BrokerNameScraper:
    def __init__(self, client=None, storage=None):
        self.client = client or MCPClient()
        self.storage = storage or ScraperDataStorage(broker_name="BrokerName")
        
    async def extract_properties(self):
        """Main method to extract properties from the broker's website."""
        # 1. Navigate to the broker's property listing page
        # 2. Get HTML content
        # 3. Take screenshots for debugging
        # 4. Parse HTML to extract property data
        # 5. Create Property objects for each listing
        # 6. Return a list of Property objects
        return property_list
```

## Runner Script Pattern

Each broker should have a dedicated runner script that follows this pattern:

```python
#!/usr/bin/env python3
"""
Runner script for the <Broker> scraper.
This script extracts property listings from <broker_website> and saves them to the database.
"""

import os
import sys
import asyncio
import logging
import json
from datetime import datetime
from pathlib import Path

# Add the project root to the Python path
script_dir = Path(__file__).resolve().parent
project_root = script_dir.parent
sys.path.insert(0, str(project_root))

# Configure logging and directory setup

async def run_<broker>_scraper_with_db():
    """
    Run the <Broker> scraper with database storage.
    """
    # Import here to allow environment variables to be set first
    from backend.scrapers.core.db_storage import DatabaseStorage
    from backend.scrapers.core.storage import ScraperDataStorage
    from backend.scrapers.brokers.<broker>.scraper import <Broker>Scraper

    # Create basic storage for HTML, screenshots, etc.
    base_storage = ScraperDataStorage(broker_name="<Broker>")
    
    # Create database storage for saving to Supabase
    db_storage = DatabaseStorage()
    
    # Create and run scraper with the base storage
    scraper = <Broker>Scraper(storage=base_storage)
    properties = await scraper.extract_properties()
    
    # Save properties to database
    for prop in properties:
        property_data = prop.to_dict()
        property_data["broker_name"] = "<Broker>"
        property_data["broker_url"] = "https://www.<broker>.com"
        
        # Save to database
        await db_storage.save_property(property_data)
    
    return len(properties)

if __name__ == "__main__":
    # Execute the scraper
    property_count = asyncio.run(run_<broker>_scraper_with_db())
```

## Testing Pattern

Each broker scraper should have comprehensive tests:

1. **Scraper Unit Tests**: Test the scraper functionality with mocked HTML content
2. **DB Storage Tests**: Test the database integration functionality

## Troubleshooting

Common issues when running broker scrapers:

1. **"No MCP client available"**: The MCP (browser automation) service isn't running or isn't accessible. 
   - Ensure the MCP server is running
   - Check that the `MCP_BASE_URL` environment variable is set correctly

2. **"Error Saving to Database"**: Issues with database connectivity
   - Verify Supabase URL and key are set correctly
   - Check database schema matches the expected format

3. **"No properties were extracted"**: The website may be down or have changed
   - Check the extracted HTML for errors (bot detection, access denied)
   - Look for new selectors if the website structure has changed

## Browser Automation with MCP

The scrapers use Model Context Protocol (MCP) for browser automation. There are three MCP implementations available:

1. **Firecrawl** (preferred): A high-performance headless browser based on Firefox
   - Best for most broker websites
   - Environment variable: `MCP_FIRECRAWL_URL` (default: `http://localhost:3000`)

2. **Playwright**: Based on the Playwright automation library
   - Better for sites with complex JavaScript or interactive elements
   - Environment variable: `MCP_PLAYWRIGHT_URL` (default: `http://localhost:3001`)

3. **Puppeteer**: Based on the Puppeteer automation library
   - Legacy option, used for compatibility with some sites
   - Environment variable: `MCP_PUPPETEER_URL` (default: `http://localhost:3002`)

To specify which MCP to use, set the `MCP_SERVER_TYPE` environment variable to one of:
- `firecrawl` (default)
- `playwright`
- `puppeteer`

Example:
```bash
MCP_SERVER_TYPE=playwright python backend/run_berkadia_scraper.py
```

Each broker website may work better with a specific MCP implementation. If a scraper is failing, try switching to a different MCP type.

### MCP Compatibility by Broker

Our testing shows the following compatibility between brokers and MCP implementations:

| Broker | Firecrawl | Playwright | Puppeteer | Notes |
|--------|-----------|------------|-----------|-------|
| Berkadia | ❌ 404 Error | ✅ Works | ❌ Fails | Playwright successfully extracts properties (12 found). Both Firecrawl and Puppeteer fail - Firecrawl returns 404 errors, Puppeteer fails with no properties. |
| Walker & Dunlop | ❌ 404 Error | ❌ 404 Error | ❌ Fails | None of the MCP implementations successfully extract properties. The website may have changed or has strong anti-scraping measures. |

For brokers not listed here, we recommend trying Playwright first, as it has shown better compatibility with modern websites that use complex JavaScript. If that fails, try Firecrawl, and finally Puppeteer.

Note: The extracted properties from Berkadia appear to be contact information rather than actual property listings. This suggests the scraper may need to be updated to target the correct elements on the website.

## Recent Updates to the Pattern

Recent improvements to the broker scraper pattern:

1. Separated storage into two types:
   - `ScraperDataStorage`: For saving HTML, screenshots, and extracted data to files
   - `DatabaseStorage`: For saving property data to Supabase

2. Added detailed error handling and logging
   - Saves HTML for debugging
   - Logs detailed information about failures
   - Detects common errors like bot detection or site unavailability

3. Runner scripts for each individual broker scraper
   - Allows running each scraper independently
   - Makes debugging easier
   - Provides a template for new broker scrapers

When implementing a new broker scraper, follow this pattern closely to ensure consistent behavior across all scrapers. 