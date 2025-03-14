# Walker & Dunlop Scraper

This module extracts multifamily property listings from the Walker & Dunlop website (https://www.walkerdunlop.com).

## Overview

Walker & Dunlop is a commercial real estate finance company offering multifamily and commercial property listings. This scraper targets the multifamily property listings to extract details like property titles, locations, units, and other relevant information.

## Implementation Details

The scraper uses Playwright through the MCP client to handle JavaScript rendering and extracts property listings using several methods:

1. **HTML Parsing**: Extracts property data from HTML elements using various CSS selectors.
2. **JSON-LD Extraction**: Looks for structured data in JSON-LD format embedded in script tags.
3. **Fallback Generic Link Analysis**: If the above methods fail, it looks for links matching property patterns.

## URL and Selectors

- **Base URL**: `https://www.walkerdunlop.com`
- **Properties URL**: `https://www.walkerdunlop.com/properties/search/property-type/multifamily/`
- **Alternative URL**: `https://www.walkerdunlop.com/properties/search/property-type/multifamily/page/1/`

The scraper tries multiple CSS selectors for property elements:
- `.property-card`
- `.property-listing`
- `.property-item`
- `.listing-item`

## Property Data Extracted

- Property Title
- Property URL
- Location/Address
- Price (if available)
- Description
- Number of Units (extracted from text if not explicitly provided)
- Square Footage (if available)

## Running the Scraper

To run the scraper, execute:

```bash
python -m backend.run_walkerdunlop_scraper.py
```

Note that our testing shows that none of the MCP implementations (Firecrawl, Playwright, or Puppeteer) currently successfully extract properties from this website.

## Dependencies

- BeautifulSoup4: For HTML parsing
- MCP Client: For browser automation with Playwright
- AsyncIO: For asynchronous programming

## Debugging

The scraper includes extensive logging and debugging features:
- HTML content is saved to `data/html/walkerdunlop/`
- Screenshots are saved to `data/screenshots/walkerdunlop/`
- Extracted data is saved to `data/extracted/walkerdunlop/`

## Error Handling

The scraper handles various error scenarios:
- Empty HTML content
- Service unavailable errors
- Access denied errors
- Bot detection

If no properties are found, the scraper attempts alternative methods and URLs.

## Notes

- The website may implement anti-scraping measures, which the scraper attempts to handle with appropriate wait times and headers.
- The number of properties extracted may vary based on website content changes.
- Testing shows that none of the MCP implementations (Firecrawl, Playwright, or Puppeteer) successfully extract properties from this website. Both Firecrawl and Playwright return 404 errors, suggesting the URLs may have changed.
- The scraper may need to be updated with new URLs and selectors to match the current website structure.
