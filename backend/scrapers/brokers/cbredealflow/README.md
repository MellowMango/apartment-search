# CBRE DealFlow Scraper

This scraper extracts property listings from the CBRE DealFlow website (https://www.cbredealflow.com).

## Overview

The CBRE DealFlow scraper is designed to extract property listings from the CBRE DealFlow website. It can operate in two modes:
1. **Public Mode**: Extracts publicly available property listings without authentication
2. **Authenticated Mode**: Uses provided credentials to log in and access additional property data

## Key Features

- Extracts property details including title, description, property type, status, and image URLs
- Handles authentication if credentials are provided
- Saves data to both local files and Supabase database
- Uses asynchronous methods for efficient operation

## Implementation Details

### MCP Client Configuration

The scraper uses the MCP (Model Context Protocol) client for browser automation. A critical configuration detail is the **port number**:

```python
# Initialize the MCP client with the correct port
browser_client = MCPClient(base_url="http://localhost:3001")
```

**Important**: The MCP server runs on port 3001 by default, not port 3000. This was a key issue that needed to be resolved for the scraper to work properly.

### Authentication

The scraper attempts to authenticate if credentials are provided in environment variables:

```
CBREDEALFLOW_USERNAME=your_username
CBREDEALFLOW_PASSWORD=your_password
```

If credentials are not provided, the scraper will still attempt to extract publicly available data.

### HTML Parsing

The scraper uses BeautifulSoup to parse the HTML and extract property listings. The key selectors for property elements are:

```python
# Main property container
property_elements = soup.select(".property_area .gridview .item")

# Property details selectors
asset_type_elem = element.select_one(".assetBar .asset")
country_elem = element.select_one(".assetBar .country")
title_elem = element.select_one(".headline a")
description_elem = element.select_one(".summary p")
status_elem = element.select_one(".status")
img_elem = element.select_one(".img img.img-responsive")
```

### Data Storage

The scraper saves data in three ways:

1. **HTML Content**: Saves the raw HTML content for debugging and analysis
2. **Extracted Data**: Saves the extracted property data as JSON files
3. **Database**: Saves the property data to Supabase (when enabled)

## Running the Scraper

### Prerequisites

1. MCP server running on port 3001
2. Environment variables set for database access:
   - `SUPABASE_URL`
   - `SUPABASE_SERVICE_ROLE_KEY`
3. Optional: CBRE DealFlow credentials in environment variables:
   - `CBREDEALFLOW_USERNAME`
   - `CBREDEALFLOW_PASSWORD`

### Command

```bash
python3 run_cbredealflow_scraper.py
```

## Troubleshooting

### MCP Connection Issues

If you encounter connection issues with the MCP server:

1. Verify the MCP server is running: `ps aux | grep -i mcp`
2. Check the port configuration in your `.env` file:
   ```
   MCP_PLAYWRIGHT_URL=http://localhost:3001
   ```
3. Ensure the scraper is using the correct port:
   ```python
   browser_client = MCPClient(base_url="http://localhost:3001")
   ```

### Authentication Issues

If the scraper fails to authenticate:

1. Verify your credentials in the `.env` file
2. Check the login selectors in the `login` method
3. Examine the HTML structure of the login page for any changes

### Data Extraction Issues

If the scraper fails to extract property data:

1. Check the HTML structure for changes in selectors
2. Examine the saved HTML files in `data/html/cbredealflow/`
3. Update the selectors in the `extract_properties` method if needed

## Development Notes

### Asynchronous Methods

The scraper uses asynchronous methods for efficient operation. Key points:

1. All methods that interact with the MCP client are asynchronous
2. The `asyncio.run()` function is used to run the main function
3. The `await` keyword is used to wait for asynchronous operations to complete

### Storage Methods

The `ScraperDataStorage` class provides methods for saving data:

1. `save_html_content`: Saves HTML content to files
2. `save_extracted_data`: Saves extracted data to JSON files
3. `save_to_database`: Saves data to Supabase and Neo4j (if configured)

## Future Improvements

1. Add more robust error handling for network issues
2. Implement pagination to extract more properties
3. Add support for filtering properties by type, location, etc.
4. Enhance data cleaning and normalization

## Features

- Handles authentication if credentials are provided
- Extracts property listings using both JavaScript data and HTML parsing
- Saves extracted data to files and optionally to a database
- Takes screenshots for verification and debugging
- Includes comprehensive logging

## Usage

### Environment Variables

The scraper uses the following environment variables:

- `CBREDEALFLOW_USERNAME`: Username for CBRE DealFlow (optional)
- `CBREDEALFLOW_PASSWORD`: Password for CBRE DealFlow (optional)

### Running the Scraper

You can run the scraper in several ways:

#### 1. Using the standalone script

```bash
python run_cbredealflow_scraper.py
```

Options:
- `--no-headless`: Run the browser in visible mode
- `--no-db`: Disable database storage

#### 2. Using the scrapers runner

```bash
python -m backend.scrapers.run_scraper --scraper cbredealflow
```

Options:
- `--no-db`: Disable database storage

#### 3. Directly from the module

```python
import asyncio
from backend.scrapers.brokers.cbredealflow.scraper import main

asyncio.run(main())
```

## Testing

To run the tests for the CBRE DealFlow scraper:

```bash
python -m unittest backend.scrapers.brokers.cbredealflow.test_cbredealflow_scraper
```

## Data Structure

The scraper extracts the following information for each property:

- Title
- Description
- Location
- Property type
- Price
- Square footage
- Number of units
- Status
- Link to the property page
- Image URL

## Dependencies

- BeautifulSoup4: For HTML parsing
- Playwright: For browser automation
- Logging: For tracking the scraping process
- Storage: For saving data to files and databases
