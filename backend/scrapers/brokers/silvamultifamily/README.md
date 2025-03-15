# Silva Multifamily Scraper

This is a specialized scraper for extracting property listings from the Silva Multifamily website (https://silvamultifamily.com/availableproperties).

## Overview

The Silva Multifamily scraper is designed to extract multifamily property listings with details such as:
- Property name
- Location
- Number of units
- Year built
- Status (Available, Under Contract, etc.)
- Property description
- Link to property details
- Price (when available)
- Square footage (when available)
- Property images (when available)

## Features

- **Multi-layered Extraction**: Uses multiple methods to extract property data:
  - JavaScript data extraction from page variables and script tags
  - HTML parsing with BeautifulSoup
  - Link analysis as a fallback
  - Table parsing for tabular data
- **Comprehensive Data Capture**: Extracts all available property details
- **Robust Error Handling**: Gracefully handles different page structures and errors
- **Database Integration**: Saves extracted properties to Supabase database
- **Debugging Tools**: Saves screenshots and HTML content for troubleshooting

## Implementation Details

The scraper uses a sophisticated approach to extract property data:

1. **JavaScript Extraction**: First attempts to extract property data directly from JavaScript variables and script tags on the page
2. **HTML Parsing**: If JavaScript extraction fails, parses the HTML content using various selectors to find property elements
3. **Link Analysis**: If no property elements are found, analyzes links on the page that might point to property listings
4. **Table Parsing**: If properties are presented in a table format, extracts data from table rows

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

## Running the Scraper

To run the scraper directly:

```bash
python3 -m backend.scrapers.brokers.silvamultifamily.scraper
```

This will:
1. Navigate to the Silva Multifamily properties page
2. Extract property listings using multiple methods
3. Save the HTML content and screenshots for debugging
4. Save the extracted properties to JSON files in `data/extracted/silvamultifamily/`
5. Save all properties to the Supabase database (if credentials are available)

## Output Structure

The scraper returns a dictionary with the following structure:

```json
{
  "success": true,
  "properties": [
    {
      "title": "Oak Ridge Apartments",
      "description": "A 24-unit apartment complex in Dallas, TX. Built in 1990.",
      "link": "https://silvamultifamily.com/properties/oak-ridge-apartments",
      "location": "Dallas, TX",
      "units": "24",
      "property_type": "Multifamily",
      "price": "$2.5 million",
      "sq_ft": "20000",
      "status": "Available",
      "image_url": "https://silvamultifamily.com/images/oak-ridge.jpg",
      "source": "Silva Multifamily",
      "year_built": "1990"
    },
    // More properties...
  ],
  "error": null
}
```

## Data Storage

The scraper stores the following data:
- Screenshots: `data/screenshots/silvamultifamily/YYYYMMDD-HHMMSS.txt`
- HTML files: `data/html/silvamultifamily/YYYYMMDD-HHMMSS.html`
- Extracted data: `data/extracted/silvamultifamily/properties-YYYYMMDD-HHMMSS.json`

## Dependencies

- BeautifulSoup4 for HTML parsing
- asyncio for asynchronous operations
- MCPClient for browser automation
- ScraperDataStorage for data storage operations
- dotenv for environment variable management

