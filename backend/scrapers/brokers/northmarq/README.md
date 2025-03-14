# NorthmarqScraper

## Overview

This scraper extracts multifamily property listings from Northmarq's website. Northmarq is a commercial real estate services company that specializes in multifamily properties, including conventional, affordable, and student housing.

## Target Website

The scraper targets the following Northmarq website:
- Main properties page: https://www.northmarq.com/properties
- Filtered URL for multifamily properties: https://www.northmarq.com/properties?property_type[]=941&property_type[]=3411&property_type[]=3306&property_type[]=3546&property_type[]=3481&property_type[]=921&property_type[]=3286&property_type[]=3296&property_type[]=3301&property_type[]=3291&property_type[]=3326&property_type[]=3551&sort_by=featured&portfolio=All

## Implementation Details

The Northmarq scraper implements the following extraction strategy:

1. Navigate to the Northmarq properties page with multifamily filters applied
2. Wait for dynamic content to load (5-second delay)
3. Extract property listings from the page
4. Extract property details including:
   - Property title
   - Location
   - Description
   - Link to the property page
   - Units (extracted from details)
   - Year built (extracted from details)
   - Property status
   - Additional property details

## Extracted Data

The scraper extracts the following fields for each property:

| Field | Description |
|-------|-------------|
| title | Name of the property |
| description | Description or property type |
| link | URL to the property details page |
| location | Location of the property |
| units | Number of units (extracted from details) |
| year_built | Year the property was built (extracted from details) |
| status | Property status (e.g., Available, Under Contract) |
| details | Full property details text |

## Running the Scraper

To run the Northmarq scraper:

```bash
python -m backend.scrapers.brokers.northmarq.scraper
```

## Testing

### Scraper Test

To test the basic functionality:

```bash
python -m backend.scrapers.brokers.northmarq.test_northmarq_scraper
```

### Database Storage Test

To test the database storage functionality:

```bash
python -m backend.scrapers.brokers.northmarq.test_db_storage
```

## Notes

- The scraper includes a 5-second delay to allow for dynamic content loading
- Property details such as units and year built are extracted from the property details text using regex patterns
- The scraper attempts to use alternative selectors if the primary selectors fail
- All extracted data is saved both to files and to the configured database (Supabase/Neo4j)
