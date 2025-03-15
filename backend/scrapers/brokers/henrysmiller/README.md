# Henry S Miller Scraper

This scraper extracts property listings from the Henry S Miller website (https://henrysmiller.com/).

## Overview

The Henry S Miller scraper is designed to extract property listings from the Henry S Miller website, focusing on commercial and multifamily properties. It uses browser automation through the MCP client to navigate the website, extract property data, and store it in both files and databases.

## Features

- Extracts property listings from the Henry S Miller website
- Handles JavaScript-rendered content
- Extracts property details such as title, location, units, price, etc.
- Saves data to files and databases (Supabase and Neo4j)
- Includes fallback mechanisms to extract data from different parts of the website

## Usage

### Running the Scraper

To run the Henry S Miller scraper:

```bash
python -m backend.scrapers.run_scraper --broker henrysmiller
```

### Testing

To run the scraper tests:

```bash
python -m pytest backend/scrapers/brokers/henrysmiller/test_henrysmiller_scraper.py -v
```

To test database storage:

```bash
python backend/scrapers/brokers/henrysmiller/test_db_storage.py
```

## Implementation Details

The scraper follows these steps:

1. Navigate to the properties page at https://henrysmiller.com/our-properties/
2. Attempt to interact with the page to load property data
3. Extract property data using multiple methods:
   - JavaScript data extraction
   - HTML parsing using various selectors
   - Extracting from property links
   - Extracting from news items
4. If no properties are found on the properties page, navigate to the home page and extract from news items
5. Save the extracted data to files and databases

## Data Structure

Each extracted property has the following structure:

```json
{
  "title": "Property Title",
  "description": "Property description",
  "link": "https://henrysmiller.com/property/example",
  "location": "123 Example St, Dallas, TX",
  "units": "10",
  "property_type": "Commercial",
  "price": "$1,000,000",
  "sq_ft": "5000",
  "status": "Available",
  "image_url": "https://henrysmiller.com/images/example.jpg",
  "source": "Henry S Miller"
}
```

## Dependencies

- BeautifulSoup4: For HTML parsing
- httpx: For HTTP requests
- MCP Client: For browser automation

## Notes

- The Henry S Miller website may not have a dedicated property listings page with structured data, so the scraper includes fallback mechanisms to extract data from news items and other parts of the website.
- The scraper is designed to be resilient to changes in the website structure by using multiple extraction methods.
