# Acquire Apartments Scrapers

This directory contains the scraper architecture for Acquire Apartments, designed to extract property listings from various broker websites.

## Directory Structure

```
scrapers/
├── core/                 # Shared utilities used by all scrapers
│   ├── mcp_client.py     # Client for interacting with MCP servers
│   ├── data_extractors.py # Utilities for extracting and structuring data
│   └── storage.py        # Data storage and organization utilities
├── brokers/              # Broker-specific scrapers
│   ├── acrmultifamily/   # ACR Multifamily scraper
│   │   ├── __init__.py
│   │   ├── acrmultifamily_scraper.py
│   │   ├── README.md     # Documentation specific to this scraper
│   │   └── test_acrmultifamily_scraper.py
│   └── [other brokers]/  # Additional broker scrapers follow the same pattern
├── helpers/              # Helper utilities
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

## Adding a New Broker

1. Create a new directory under `brokers/` with your broker name
2. Implement the necessary files (see the `acrmultifamily` directory as an example)
3. Register your scraper in `run_scraper.py`

See the [Scraper Architecture](../../docs/scraper-architecture.md) and [Scraper Usage Guide](../../docs/scraper-usage-guide.md) for detailed instructions.

## Core Components

### MCP Client

The `MCPClient` class in `core/mcp_client.py` provides a wrapper around the Model Context Protocol (MCP) server API, which drives browser automation for scraping.

### Data Extractors

The `PropertyExtractor` class in `core/data_extractors.py` contains methods for extracting and structuring property data from HTML content.

### Storage

The `DataStorage` class in `core/storage.py` handles saving screenshots, HTML content, and extracted data in an organized manner.

## Testing

Each broker scraper should have a corresponding test file. Run the tests with:

```bash
python -m pytest backend/scrapers/brokers/acrmultifamily/test_acrmultifamily_scraper.py -v
```

## Documentation

For more detailed documentation, see:

- [Scraper Architecture](../../docs/scraper-architecture.md): Detailed overview of the scraper system
- [Scraper Usage Guide](../../docs/scraper-usage-guide.md): Instructions for using and extending the scraper system
- Individual broker READMEs (e.g., `brokers/acrmultifamily/README.md`): Broker-specific details and notes 

## Database Storage

The scrapers now support saving data directly to both Supabase and Neo4j databases through the `save_to_database` method in the `DataStorage` class.

### How it Works

1. The `save_to_database` method in `core/storage.py` extracts property data from the scraper output
2. It connects to both Supabase and Neo4j using the clients in `app/db/`
3. For each property, it:
   - Generates a UUID for the property
   - Maps scraped data to the database schema
   - Inserts the property into Supabase
   - Inserts the property into Neo4j
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
| link          | property_website | Link to the property listing |
| description   | description    | Property description | 