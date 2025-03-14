# MarcusmillichapScraper

## Overview

This scraper extracts multifamily property listings from marcusmillichap's website. marcusmillichap is a commercial real estate services company that lists various property types, including multifamily properties.

## Target Website

The scraper targets the following marcusmillichap website:
- Main properties page: https://www.marcusmillichap.com/properties

## Implementation Details

The marcusmillichap scraper implements the following extraction strategy:

1. Navigate to the marcusmillichap properties page
2. Extract property listings from the page
3. Extract property details including:
   - Property title
   - Location
   - Description
   - Link to the property page
   - Units (if available)
   - Year built (if available)

## Extracted Data

The scraper extracts the following fields for each property:

| Field | Description |
|-------|-------------|
| title | Name of the property |
| description | Description or property type |
| link | URL to the property details page |
| location | Location of the property |
| units | Number of units (if available) |
| year_built | Year the property was built (if available) |
| status | Property status (defaults to "Available") |

## Running the Scraper

To run the marcusmillichap scraper:

```bash
python -m backend.scrapers.brokers.marcusmillichap.scraper
```

## Testing

### Scraper Test

To test the basic functionality:

```bash
python -m backend.scrapers.brokers.marcusmillichap.test_marcusmillichap_scraper
```

### Database Storage Test

To test the database storage functionality:

```bash
python -m backend.scrapers.brokers.marcusmillichap.test_db_storage
```

## Notes

- The scraper implementation may need to be adjusted based on the specific structure of the marcusmillichap website.
- Property details such as units and year built may not be consistently available on the listings page and might require fetching individual property detail pages.
