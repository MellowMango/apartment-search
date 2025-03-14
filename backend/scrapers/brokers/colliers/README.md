# Colliers Scraper

## Overview

This scraper extracts multifamily property listings from Colliers' website. Colliers is a leading global real estate services and investment management company that lists various property types, including multifamily properties, for investment sales.

## Target Website

The scraper targets the following Colliers website:
- Main sales properties page: https://sales.colliers.com/
- Filtered URL for multifamily properties: https://sales.colliers.com/?q=multifamily

## Implementation Details

The Colliers scraper implements the following extraction strategy:

1. Navigate to the Colliers sales page with multifamily property filter applied
2. Wait for dynamic content to load (12-second delay)
3. Extract property listings from the page using multiple selector strategies:
   - First try with common property card class names
   - Fall back to more generic selectors if needed
   - Try extracting from links if structured cards aren't found
4. For each property, extract details including:
   - Property title
   - Link to property details
   - Location
   - Description
   - Units count (extracted using regex patterns)
   - Property type
   - Price
   - Square footage
   - Property image URL
   - Contact information (if available)
5. Handle pagination to extract properties from multiple pages

## Extracted Data

The scraper extracts the following fields for each property:

| Field | Description |
|-------|-------------|
| title | Name of the property |
| description | Description or summary |
| link | URL to the property details page |
| location | Location of the property |
| units | Number of units (extracted using regex patterns) |
| property_type | Type of property (e.g., "Multifamily", "Apartment") |
| price | Listed price of the property (if available) |
| sq_ft | Square footage of the property (if available) |
| status | Property status (e.g., Available, Under Contract) |
| image_url | URL to the property image (if available) |
| source | Set to "Colliers" to identify the broker source |

## Running the Scraper

To run the Colliers scraper:

```bash
python -m backend.scrapers.brokers.colliers.scraper
```

## Testing

### Scraper Test

To test the basic functionality:

```bash
python -m backend.scrapers.brokers.colliers.test_colliers_scraper
```

### Database Storage Test

To test the database storage functionality:

```bash
python -m backend.scrapers.brokers.colliers.test_db_storage
```

## Notes

- The scraper includes a 12-second delay to allow for dynamic content loading
- Multiple strategies are employed to find property listings as the site structure may vary
- Robust regex patterns are used to extract units, price, and square footage information
- The extracted data is saved both to files and to the configured database (Supabase/Neo4j)
- Pagination is handled to extract properties from all available pages
