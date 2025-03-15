# GoGetters Multifamily Scraper

## Overview

This scraper extracts multifamily property listings from GoGetters Multifamily's website. GoGetters Multifamily is a specialized broker focusing on multifamily investment properties across various markets.

## Target Website

The scraper targets the following URL:
- Main listings page: https://www.gogettersmultifamily.com/current-listings

## Implementation Details

The GoGetters Multifamily scraper implements the following extraction strategy:

1. Navigate to the GoGetters current listings page
2. Wait for dynamic content to load (10-second delay)
3. Extract property listings from the page using multiple selector strategies:
   - First try with common property card class names
   - Fall back to more generic selectors if needed
   - Try extracting from sections that might contain property listings
   - As a last resort, look for any divs containing images and headings
   - If all else fails, extract from property-related links
4. For each property, extract details including:
   - Property title
   - Link to property details
   - Location
   - Description
   - Units count (extracted using regex patterns)
   - Property type
   - Price
   - Square footage
   - Status (Available, Under Contract, Sold)
   - Property image URL

## Extracted Data

The scraper extracts the following fields for each property:

| Field | Description |
|-------|-------------|
| title | Name of the property |
| description | Description or summary |
| link | URL to the property details page |
| location | Location of the property |
| units | Number of units (extracted using regex patterns) |
| property_type | Type of property (typically "Multifamily") |
| price | Listed price of the property (if available) |
| sq_ft | Square footage of the property (if available) |
| status | Property status (e.g., Available, Under Contract, Sold) |
| image_url | URL to the property image (if available) |
| source | Set to "GoGetters Multifamily" to identify the broker source |

## Running the Scraper

To run the GoGetters Multifamily scraper:

```bash
python -m backend.scrapers.brokers.gogetters.scraper
```

## Testing

### Scraper Test

To test the basic functionality:

```bash
python -m backend.scrapers.brokers.gogetters.test_gogetters_scraper
```

### Database Storage Test

To test the database storage functionality:

```bash
python -m backend.scrapers.brokers.gogetters.test_db_storage
```

## Notes

- The scraper includes a 10-second delay to allow for dynamic content loading
- Multiple strategies are employed to find property listings as the site structure may vary
- Robust regex patterns are used to extract units, price, and square footage information
- The extracted data is saved both to files and to the configured database (Supabase/Neo4j)
- The scraper is designed to be resilient to changes in the website structure by using multiple fallback methods for finding and extracting property data 