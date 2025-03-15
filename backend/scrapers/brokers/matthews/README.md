# Matthews.com Scraper

This scraper extracts property listings from the Matthews.com website.

## Overview

Matthews is a commercial real estate brokerage firm that specializes in investment sales, leasing, and debt and equity services. The scraper extracts property listings from their website, including details such as:

- Property title
- Location
- Price
- Property type
- Status
- Images

## Usage

To run the scraper:

```bash
cd backend
python debug_matthews_scraper.py
```

## Implementation Details

The scraper works by:

1. Navigating to the Matthews.com listings page
2. Capturing a screenshot for debugging purposes
3. Saving the HTML content
4. Parsing the HTML to extract property listings
5. Saving the extracted data to both files and database

The scraper uses multiple CSS selectors to find property listings, with fallbacks in case the primary selector doesn't work. This makes it more robust to website changes.

## Data Structure

Each property is extracted with the following fields:

- `source`: "matthews"
- `source_id`: Unique identifier for the property
- `url`: URL to the property listing
- `title`: Title of the property
- `description`: Description of the property (if available)
- `location`: Location of the property
- `property_type`: Type of property (e.g., Retail, Office, Industrial)
- `units`: Number of units (if applicable)
- `year_built`: Year the property was built (if available)
- `price`: Price of the property (if available)
- `status`: Status of the property (e.g., Active, Under Contract)
- `images`: List of image URLs for the property
