# Scraper Usage Guide

This guide provides instructions on how to use the Acquire Apartments scraper system to collect property listings from various broker websites.

## Prerequisites

1. Ensure you have the required dependencies installed:
   ```bash
   pip install -r requirements.txt
   ```

2. Make sure an MCP server is running. You can start it with:
   ```bash
   docker-compose up mcp-server
   ```
   
   Or run the standalone Firecrawl MCP server:
   ```bash
   cd mcp-server
   python run_server.py
   ```

## Running Scrapers

### Command-Line Interface

The scraper system provides a convenient command-line interface via `run_scraper.py`:

```bash
cd backend/scrapers
python run_scraper.py --help
```

#### Run a specific broker scraper:

```bash
python run_scraper.py --broker acrmultifamily
```

#### Run all available scrapers:

```bash
python run_scraper.py --all
```

#### Specify custom output directories:

```bash
python run_scraper.py --broker acrmultifamily --output-dir /custom/path
```

#### Enable verbose logging:

```bash
python run_scraper.py --broker acrmultifamily --verbose
```

### Programmatic Usage

You can also use the scrapers programmatically in your Python code:

```python
from backend.scrapers.brokers.acrmultifamily.acrmultifamily_scraper import ACRMultifamilyScraper

# Initialize the scraper
scraper = ACRMultifamilyScraper(
    mcp_server_url="http://localhost:8000",
    output_dir="data"
)

# Run the scraper
properties = scraper.scrape()

# Access the extracted properties
for prop in properties:
    print(f"Property: {prop.name}")
    print(f"Location: {prop.location}")
    print(f"Price: {prop.price}")
    print(f"Details: {prop.details}")
    print("---")

# Save the results to storage
scraper.save_results(properties)
```

## Output and Data Files

The scraper system organizes data in the following structure:

- `data/screenshots/<broker>/`: Contains screenshot captures during scraping
- `data/html/<broker>/`: Contains HTML source of the pages scraped
- `data/extracted/<broker>/`: Contains JSON files with extracted property data

Each file is timestamped for tracking and troubleshooting purposes.

## Adding a New Broker

To add a new broker scraper:

1. Create a new directory under `backend/scrapers/brokers/`:
   ```bash
   mkdir -p backend/scrapers/brokers/new_broker_name
   ```

2. Create the broker-specific scraper files:
   - `__init__.py`: Package initialization
   - `new_broker_scraper.py`: Main scraper implementation
   - `README.md`: Documentation for this specific broker
   - `test_new_broker_scraper.py`: Tests for this scraper

3. Implement the scraper by extending the base classes:
   ```python
   # new_broker_scraper.py
   from backend.scrapers.core.mcp_client import MCPClient
   from backend.scrapers.core.data_extractors import PropertyExtractor
   from backend.scrapers.core.storage import DataStorage
   
   class NewBrokerScraper:
       """Scraper for NewBroker properties."""
       
       def __init__(self, mcp_server_url="http://localhost:8000", output_dir="data"):
           self.client = MCPClient(mcp_server_url)
           self.extractor = PropertyExtractor()
           self.storage = DataStorage(output_dir, "new_broker")
           self.base_url = "https://www.newbroker.com/properties"
       
       def scrape(self):
           # Implement broker-specific scraping logic
           # ...
           return properties
   ```

4. Register the new scraper in `run_scraper.py`.

5. Test the new scraper:
   ```bash
   python run_scraper.py --broker new_broker_name
   ```

## Troubleshooting

### Common Issues

1. **MCP Server Connection Errors**:
   - Ensure the MCP server is running
   - Check the URL and port configuration
   - Verify network connectivity

2. **No Properties Found**:
   - Inspect the screenshot files in `data/screenshots/<broker>/`
   - Check the HTML files in `data/html/<broker>/`
   - Review the browser console logs for JavaScript errors
   - The broker website may have changed layout or structure

3. **Rate Limiting or Blocking**:
   - Implement delays between requests
   - Consider using proxy rotation
   - Modify User-Agent headers

### Viewing Logs

Logs are stored in the `logs/` directory with timestamps. To view the latest log:

```bash
tail -f logs/scraper-latest.log
```

## Advanced Features

### Webhook Notifications

Configure webhook notifications when new properties are found:

```python
scraper = ACRMultifamilyScraper(
    mcp_server_url="http://localhost:8000",
    output_dir="data",
    webhook_url="https://your-webhook-endpoint.com/new-property"
)
```

### Scheduling Regular Scrapes

Use the built-in scheduler to run scrapers at regular intervals:

```bash
python -m backend.scrapers.scheduler --broker acrmultifamily --interval 6h
```

This will run the specified scraper every 6 hours.

## Additional Resources

- [Scraper Architecture Documentation](scraper-architecture.md)
- [Tech Stack Overview](tech-stack.md)
- [Database Integration Guide](supabase-setup.md) 