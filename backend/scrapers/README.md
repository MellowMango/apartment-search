# Acquire Apartments Scrapers

This directory contains the scraper architecture for Acquire Apartments, designed to extract property listings from various broker websites and store them in both local files and databases.

## Directory Structure

```
scrapers/
├── core/                 # Shared utilities used by all scrapers
│   ├── mcp_client.py     # Client for interacting with MCP servers
│   ├── data_extractors.py # Utilities for extracting and structuring data
│   └── storage.py        # Data storage and database integration utilities
├── brokers/              # Broker-specific scrapers
│   ├── acrmultifamily/   # ACR Multifamily scraper
│   │   ├── __init__.py
│   │   ├── scraper.py    # Main scraper implementation
│   │   ├── test_acrmultifamily_scraper.py # Tests for scraper
│   │   ├── test_db_storage.py # Tests for database storage
│   │   └── README.md     # Documentation specific to this scraper
│   └── [other brokers]/  # Additional broker scrapers follow the same pattern
├── aggregators/          # Aggregation utilities for combining data from multiple sources
├── helpers/              # Helper utilities
├── tests/                # Shared test utilities and integration tests
├── run_scraper.py        # Command-line interface for running scrapers
└── README.md             # This file
```

## Quick Start

### Running a Scraper

To run a specific broker scraper:

```bash
python run_scraper.py --broker acrmultifamily
```

To run all available scrapers:

```bash
python run_scraper.py --all
```

For more options:

```bash
python run_scraper.py --help
```

### Output

Scrapers store their output in the `data/` directory:

- Screenshots: `data/screenshots/<broker>/`
- HTML content: `data/html/<broker>/`
- Extracted data: `data/extracted/<broker>/`

Additionally, all extracted property data is stored in both Supabase and Neo4j databases.

## Adding a New Broker Scraper

1. Create a new directory under `brokers/` with your broker name (e.g., `brokers/newbroker/`)
2. Create the following files:
   - `__init__.py` - Package initialization
   - `scraper.py` - Main scraper implementation
   - `test_<broker>_scraper.py` - Tests for the scraper
   - `test_db_storage.py` - Tests for database storage
   - `README.md` - Documentation specific to this scraper
3. Implement the scraper class following the `ACRMultifamilyScraper` example:
   ```python
   from scrapers.core.mcp_client import MCPClient
   from scrapers.core.storage import DataStorage
   
   class NewBrokerScraper:
       def __init__(self, client=None, storage=None):
           self.client = client or MCPClient()
           self.storage = storage or DataStorage("newbroker")
       
       async def extract_properties(self):
           # Implement property extraction logic
           # Save to files and database
           return result
   ```
4. Register your scraper in `run_scraper.py`

See the [Scraper Architecture](../../docs/scraper-architecture.md) and [Scraper Usage Guide](../../docs/scraper-usage-guide.md) for detailed instructions.

## Core Components

### MCP Client

The `MCPClient` class in `core/mcp_client.py` provides a wrapper around the Model Context Protocol (MCP) server API, which drives browser automation for scraping. It supports both local and remote MCP servers.

Key methods:
- `navigate(url)`: Navigate to a URL
- `get_html()`: Get the current page's HTML
- `take_screenshot()`: Take a screenshot of the current page
- `execute_script(script)`: Execute JavaScript on the page

### Data Extractors

The `PropertyExtractor` class in `core/data_extractors.py` contains methods for extracting and structuring property data from HTML content. It provides utilities for parsing common property data formats.

### Storage

The `DataStorage` class in `core/storage.py` handles:
1. Saving screenshots, HTML content, and extracted data in an organized file structure
2. Saving extracted property data to Supabase and Neo4j databases

## Database Storage

The scrapers now successfully save data to both Supabase and Neo4j databases through the `save_to_database` method in the `DataStorage` class.

### How it Works

1. The `save_to_database` method in `core/storage.py` extracts property data from the scraper output
2. It connects to both Supabase and Neo4j using the clients in `app/db/`
3. For each property, it:
   - Generates a UUID for the property
   - Maps scraped data to the database schema
   - Inserts the property into Supabase
   - Attempts to insert the property into Neo4j
   - Logs the results

### Usage

To save scraped data to the database:

```python
# Inside your scraper class
async def extract_properties(self):
    # ... extract data ...
    
    # Save to files
    self.storage.save_extracted_data(results, "properties", timestamp)
    
    # Save to database
    await self.storage.save_to_database(results, "properties")
```

### Required Environment Variables

The following environment variables need to be set:

- For Supabase:
  - `SUPABASE_URL`: The URL of your Supabase project
  - `SUPABASE_SERVICE_ROLE_KEY`: Service role key for Supabase

- For Neo4j:
  - `NEO4J_URI`: The URI of your Neo4j database
  - `NEO4J_USERNAME`: Neo4j database username
  - `NEO4J_PASSWORD`: Neo4j database password
  - `NEO4J_DATABASE`: Neo4j database name (defaults to "neo4j")

### Data Mapping

The scraped property data is mapped to the database schema as follows:

| Scraped Field | Database Field | Notes |
|---------------|----------------|-------|
| title         | name           | Property name/title |
| location      | address, city, state | Parsed from the location string |
| units         | units          | Number of units in the property |
| year_built    | year_built     | Year the property was built |
| status        | property_status| Property status (active, pending, etc.) |
| description   | description    | Property description | 

## Testing

Each broker scraper should have both standard unit tests and database storage tests:

```bash
# Run standard scraper tests
python -m pytest backend/scrapers/brokers/acrmultifamily/test_acrmultifamily_scraper.py -v

# Run database storage tests
python backend/scrapers/brokers/acrmultifamily/test_db_storage.py
```

## Troubleshooting

### MCP Server Issues

If you encounter issues with the MCP server:
1. Ensure the MCP server is running (`docker compose up mcp`)
2. Check that the MCP server URL is correct in your environment variables
3. Verify the browser automation is working by checking the screenshots

### Database Connection Issues

If you encounter issues saving to the database:
1. Verify your environment variables are set correctly
2. Check database connection with `python force_env_test.py`
3. Examine the schema compatibility between extracted data and database tables

## Documentation

For more detailed documentation, see:

- [Scraper Architecture](../../docs/scraper-architecture.md): Detailed overview of the scraper system
- [Scraper Usage Guide](../../docs/scraper-usage-guide.md): Instructions for using and extending the scraper system
- Individual broker READMEs (e.g., `brokers/acrmultifamily/README.md`): Broker-specific details and notes 