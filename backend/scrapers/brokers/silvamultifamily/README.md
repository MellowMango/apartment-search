# Silva Multifamily Scraper

This is a specialized scraper for extracting property listings from the Silva Multifamily website (https://silvamultifamily.com/availableproperties).

## Overview

The Silva Multifamily scraper is designed to extract property listings with details such as:
- Property name
- Location
- Number of units
- Year built
- Status (Available, Under Contract, etc.)
- Property description
- Link to property details

## Website Structure

Silva Multifamily's website displays property listings with the following characteristics:
- Properties are typically displayed in a grid or card format
- Each property has a title and may include a description
- Details like location, units, and year built may be included in structured elements or within the description text
- Links to detailed property pages are often provided

## Usage

```python
from backend.scrapers.brokers.silvamultifamily.scraper import SilvaMultifamilyScraper

async def run_scraper():
    scraper = SilvaMultifamilyScraper()
    results = await scraper.extract_properties()
    
    if results.get("success"):
        properties = results.get("properties", [])
        print(f"Extracted {len(properties)} properties")
        for prop in properties:
            print(f"- {prop['title']} ({prop.get('location', 'Unknown')})")
    else:
        print(f"Error: {results.get('error')}")

# Then call the function with asyncio.run(run_scraper())
```

## Output Structure

The scraper returns a dictionary with the following structure:

```json
{
  "url": "https://silvamultifamily.com/availableproperties",
  "title": "Available Properties | Silva Multifamily",
  "analyzed_at": "2025-03-13 15:47:37.444316",
  "success": true,
  "properties": [
    {
      "title": "Oak Ridge Apartments",
      "description": "A 24-unit apartment complex in Dallas, TX. Built in 1990.",
      "link": "https://silvamultifamily.com/properties/oak-ridge-apartments",
      "location": "Dallas, TX",
      "units": "24",
      "year_built": "1990",
      "status": "Available"
    },
    // More properties...
  ]
}
```

## Data Storage

The scraper stores the following data:
- Screenshots: `data/screenshots/silvamultifamily/YYYYMMDD-HHMMSS.txt`
- HTML files: `data/html/silvamultifamily/YYYYMMDD-HHMMSS.html`
- HTML previews: `data/html/silvamultifamily/preview-YYYYMMDD-HHMMSS.txt`
- Extracted data: `data/extracted/silvamultifamily/properties-YYYYMMDD-HHMMSS.json`

## Dependencies

- BeautifulSoup4 for HTML parsing
- httpx for async HTTP requests
- MCP Client for browser automation

