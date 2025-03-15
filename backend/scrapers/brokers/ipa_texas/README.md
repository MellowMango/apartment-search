# IPA Texas Multifamily Scraper

This scraper extracts multifamily property listings from the IPA Texas Multifamily website (https://ipatexasmultifamily.com).

## Status

- **Development Status**: Initial implementation
- **Last Updated**: Current date
- **Functionality**: The scraper is designed to extract property listings from the IPA Texas Multifamily website, including property details such as title, description, location, units, year built, price, status, and images.

## Technical Details

The scraper performs the following operations:

1. Navigates to the IPA Texas Multifamily properties page
2. Takes a screenshot for debugging purposes
3. Saves the HTML content of the page
4. Extracts property data from the HTML content
5. Handles pagination to extract properties from multiple pages
6. Saves the extracted data to both Supabase and Neo4j databases

## Implementation

The scraper uses the following technologies:

- **Browser Automation**: Uses the MCP client with Playwright for browser automation
- **HTML Parsing**: Uses BeautifulSoup for HTML parsing
- **Data Storage**: Saves data to both Supabase and Neo4j databases

## Usage

To run the scraper:

```bash
python3 scrapers/run_scraper.py --scraper ipa_texas
```

## Property Data Structure

The scraper extracts the following data for each property:

- `source`: The source of the data (always "ipa_texas")
- `source_id`: A unique identifier for the property
- `url`: The URL of the property detail page
- `title`: The title or name of the property
- `description`: A description of the property
- `location`: The location or address of the property
- `property_type`: The type of property (always "Multifamily")
- `units`: The number of units in the property
- `year_built`: The year the property was built
- `price`: The price or asking price of the property
- `status`: The status of the property (e.g., "Active", "Under Contract")
- `images`: A list of image URLs for the property

## Notes

- The scraper is designed to be robust and handle various HTML structures that might be present on the IPA Texas Multifamily website.
- Error handling is implemented to ensure that the scraper continues to function even if some properties cannot be extracted.
- Logging is implemented to track the progress of the scraper and identify any issues that might arise. 