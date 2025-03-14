# JLL Scraper

## Overview

This scraper extracts multifamily property listings from JLL's website. JLL (Jones Lang LaSalle) is a global commercial real estate services company that lists various property types, including multifamily properties.

## Target Website

The scraper targets the following JLL websites:
- Main multifamily section: https://www.us.jll.com/en/industries/multifamily
- Properties for sale: https://www.us.jll.com/en/properties

## Implementation Details

The JLL scraper implements the following extraction strategy:

1. Navigate to the JLL multifamily industry page
2. Extract property listings from the "Multifamily investment opportunities" section
3. If no properties are found, attempt to find property links elsewhere on the page
4. As a fallback, try to find and navigate to the "Multifamily properties for sale" link
5. Extract property details including:
   - Property title
   - Location
   - Description/property type
   - Link to the property page

The scraper handles variations in JLL's website structure by implementing multiple extraction strategies.

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

To run the JLL scraper:

```bash
python -m backend.scrapers.brokers.jll.scraper
```

## Testing

### Scraper Test

To test the basic functionality:

```bash
python -m backend.scrapers.brokers.jll.test_jll_scraper
```

### Database Storage Test

To test the database storage functionality:

```bash
python -m backend.scrapers.brokers.jll.test_db_storage
```

## Notes

- JLL's website structure may change over time, requiring updates to the extraction selectors.
- The scraper implements multiple fallback strategies to handle different page structures.
- Property details such as units and year built may not be consistently available on JLL's listings page and might require fetching individual property detail pages.
