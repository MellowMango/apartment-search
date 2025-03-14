# ACR Multifamily Scraper

This is a specialized scraper for extracting property listings from the ACR Multifamily website (https://www.acrmultifamily.com/properties).

## Overview

The ACR Multifamily scraper is designed to extract property listings with details such as:
- Property name
- Location
- Number of units
- Year built
- Status (Available, Closed, etc.)
- Property description
- Link to property details

## Website Structure

ACR Multifamily is built on Squarespace and has a specific structure for property listings:
- Properties are displayed in a list
- Each property has a title (`.list-item-content__title`)
- Each property has a description (`.list-item-content__description`)
- Some properties have links to detail pages

## Usage

```python
from backend.scrapers.brokers.acrmultifamily.scraper import ACRMultifamilyScraper

async def run_scraper():
    scraper = ACRMultifamilyScraper()
    results = await scraper.extract_properties()
    
    if results.get("success"):
        properties = results.get("properties", [])
        print(f"Extracted {len(properties)} properties")
        for prop in properties:
            print(f"- {prop['title']} ({prop['location']}): {prop['units']} units")
    else:
        print(f"Error: {results.get('error')}")

# Then call the function with asyncio.run(run_scraper())
```

## Output Structure

The scraper returns a dictionary with the following structure:

```json
{
  "url": "https://www.acrmultifamily.com/properties",
  "title": "Properties | ACR Multifamily",
  "analyzed_at": "2025-03-13 15:47:37.444316",
  "success": true,
  "properties": [
    {
      "title": "Boerne Villas",
      "description": "MARKET PRICING\nLocation: Boerne, TX\nYear Built: 1970\nUnits: 16\nStatus: Available",
      "link": "https://www.acrmultifamily.com/boerne-villas",
      "location": "Boerne, TX",
      "units": "16",
      "year_built": "1970",
      "status": "Available"
    },
    // More properties...
  ]
}
```

## Data Storage

The scraper stores the following data:
- Screenshots: `data/screenshots/acrmultifamily/YYYYMMDD-HHMMSS.txt`
- HTML files: `data/html/acrmultifamily/YYYYMMDD-HHMMSS.html`
- HTML previews: `data/html/acrmultifamily/preview-YYYYMMDD-HHMMSS.txt`
- Extracted data: `data/extracted/acrmultifamily/properties-YYYYMMDD-HHMMSS.json`

## Dependencies

- BeautifulSoup4 for HTML parsing
- httpx for async HTTP requests
- MCP Client for browser automation 