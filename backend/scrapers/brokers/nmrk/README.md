# NmrkScraper

## Overview

This scraper extracts multifamily property listings from Newmark's website. Newmark (NMRK) is a leading commercial real estate services firm that lists various property types, including multifamily properties, for investment sales.

## Target Website

The scraper targets the following Newmark website:
- Main properties page: https://www.nmrk.com/properties/investment-sales
- Filtered URL for multifamily properties: https://www.nmrk.com/properties/investment-sales?propertyType=Multifamily&tab=properties

## Implementation Details

The Newmark scraper implements the following extraction strategy:

1. Navigate to the Newmark investment sales page with multifamily property filter applied
2. Wait for dynamic content to load (12-second delay)
3. Attempt JavaScript extraction of property data from window objects
4. Extract property listings from the page using multiple selector strategies:
   - First try with common property card class names
   - Fall back to more generic selectors if needed
   - Try data attribute selectors as a final approach
5. For each property, extract details including:
   - Property title
   - Link to property details
   - Location
   - Description
   - Units count (extracted using regex patterns)
   - Year built (extracted using regex patterns)
   - Status
   - Price
   - Property image URL

## Extracted Data

The scraper extracts the following fields for each property:

| Field | Description |
|-------|-------------|
| title | Name of the property |
| description | Description or property type |
| link | URL to the property details page |
| location | Location of the property |
| units | Number of units (extracted using regex patterns) |
| year_built | Year the property was built (extracted using regex patterns) |
| status | Property status (e.g., Available, Under Contract) |
| price | Listed price of the property (if available) |
| image_url | URL to the property image (if available) |

## Running the Scraper

To run the Newmark scraper:

```bash
python -m backend.scrapers.brokers.nmrk.scraper
```

## Testing

### Scraper Test

To test the basic functionality:

```bash
python -m backend.scrapers.brokers.nmrk.test_nmrk_scraper
```

### Database Storage Test

To test the database storage functionality:

```bash
python -m backend.scrapers.brokers.nmrk.test_db_storage
```

## Notes

- The scraper includes a 12-second delay to allow for dynamic content loading
- Multiple strategies are employed to find property listings as the site structure may vary
- Robust regex patterns are used to extract units and year built information from various text elements
- The scraper implements an alternative approach that looks for property links if standard property cards aren't found
- Images URLs are captured when available to enhance property listings
- The extracted data is saved both to files and to the configured database (Supabase/Neo4j)
