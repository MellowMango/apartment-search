# Berkadia Scraper

This module extracts multifamily property listings from the Berkadia website (https://www.berkadia.com).

## Overview

Berkadia is a joint venture between Berkshire Hathaway and Jefferies Financial Group, offering commercial real estate services, including multifamily property listings. This scraper targets the multifamily property listings to extract details like property titles, locations, units, and other relevant information.

## Implementation Details

The scraper uses Playwright through the MCP client to handle JavaScript rendering and extracts property listings using several methods:

1. **HTML Parsing**: Extracts property data from HTML elements using various CSS selectors.
2. **JSON Script Extraction**: Looks for structured data embedded in script tags, including JSON-LD and JavaScript variable assignments.
3. **API Data Fetching**: Attempts to identify and fetch data from API endpoints discovered in the HTML content.
4. **Fallback Generic Link Analysis**: If the above methods fail, it looks for links matching property patterns.

## URL and Selectors

- **Base URL**: `https://www.berkadia.com`
- **Properties URLs**:
  - `https://www.berkadia.com/properties/`
  - `https://www.berkadia.com/properties/multi-family/`
  - `https://www.berkadia.com/investment-sales/listings/`

The scraper tries multiple CSS selectors for property elements:
- `.property-listing`
- `.property-card`
- `.listing-item`
- `.property-grid-item`

## Property Data Extracted

- Property Title
- Property URL
- Location/Address
- Price (if available)
- Description
- Number of Units (extracted from text if not explicitly provided)
- Square Footage (if available)
- Year Built (if available)

## Running the Scraper

To run the scraper, execute:

```bash
python -m backend.run_berkadia_scraper.py
```

For best results, use the Playwright MCP implementation:

```bash
MCP_SERVER_TYPE=playwright python -m backend.run_berkadia_scraper.py
```

## Dependencies

- BeautifulSoup4: For HTML parsing
- MCP Client: For browser automation with Playwright
- AsyncIO: For asynchronous programming
- RegEx: For pattern matching in text and JavaScript extraction

## Debugging

The scraper includes extensive logging and debugging features:
- HTML content is saved to `data/html/berkadia/`
- Screenshots are saved to `data/screenshots/berkadia/`
- Extracted data is saved to `data/extracted/berkadia/`

## Error Handling

The scraper handles various error scenarios:
- Empty HTML content
- Service unavailable errors
- Access denied errors
- Bot detection
- Failed API requests

If no properties are found, the scraper attempts alternative methods and URLs.

## API Data Extraction

The scraper automatically looks for potential API endpoints in the JavaScript code by scanning for patterns like:
- `fetch()` or `axios.get()` calls
- URL assignments to variables
- API endpoint definitions

If API endpoints are found, the scraper attempts to fetch data from them and process it into property listings.

## Notes

- The website may implement anti-scraping measures, which the scraper attempts to handle with appropriate wait times and headers.
- The number of properties extracted may vary based on website content changes and the effectiveness of the different extraction methods.
- Testing shows that only the Playwright MCP implementation successfully extracts data from this website. Firecrawl returns 404 errors, and Puppeteer fails to extract any properties.
- The extracted data appears to be contact information rather than property listings, suggesting that the website structure may have changed. The scraper selectors may need to be updated to target the correct elements.
