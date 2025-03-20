# Data Enrichment & Deep Property Research

This module provides comprehensive property data enrichment and deep research capabilities, using both direct API integration and the Microsoft open-deep-research MCP server for advanced analysis.

## Features

### Basic Data Enrichment
- **Geocoding**: Convert property addresses to latitude and longitude coordinates using multiple providers (Google Maps, Mapbox, Nominatim/OpenStreetMap)
- **Property Details Enhancement**: Extract and enhance property details from available data
- **Neighborhood Data**: Add neighborhood information such as Walk Score and nearby amenities
- **Image Enhancement**: Find additional property images from public sources
- **Text Extraction**: Extract structured data from unstructured property descriptions

### Deep Property Research (NEW)
- **Comprehensive Property Profiling**: Ownership history, unit mix, construction details, zoning, and historical performance
- **Investment Metrics Analysis**: Cap rates, NOI estimation, value-add opportunities, and investment scenarios
- **Market Intelligence**: Competitive landscape, rental trends, supply/demand metrics, and market projections
- **Risk & Blindspot Analysis**: Identify potential risks, legal issues, maintenance concerns, and market vulnerabilities
- **AI-Powered Research**: Leverage Microsoft's open-deep-research MCP for sophisticated property analysis

## Testing Guide

The data enrichment system can be tested using various approaches:

### Unit Testing
Run individual unit tests for each component:

```bash
# Test database extensions
python -m pytest backend/tests/test_db_extensions.py -v

# Test specific enrichers
python -m pytest backend/tests/test_enrichers.py -v

# Test property researcher
python -m pytest backend/tests/test_property_researcher.py -v
```

### Integration Testing
Test the entire enrichment pipeline:

```bash
# Test the complete enrichment pipeline
python -m pytest backend/tests/test_integration.py -v

# Test with diagnostic output
python -m pytest backend/tests/test_enrichment_diagnostics.py -v
```

### Manual Testing with CLI
Use the CLI for manual testing on real data:

```bash
# Test with a single property
python -m backend.data_enrichment.cli research --property-id <UUID> --depth basic

# Test batch processing with limited properties
python -m backend.data_enrichment.cli batch-research --limit 5 --concurrency 2 --depth basic
```

### Testing Best Practices

1. **Mock External APIs**: Use mock responses for all external API calls to ensure tests are reliable
2. **Cache Testing**: Verify cache hit/miss behavior using controlled test data
3. **Database Testing**: Use temporary test databases or transaction rollbacks
4. **Concurrency Testing**: Test batch operations with various concurrency settings
5. **Error Handling**: Specifically test system recovery behavior when APIs fail
6. **Geocoding Testing**: Test geocoding with varied address formats and provider fallbacks

```bash
# Test geocoding functionality
python -m backend.data_enrichment.test_geocoding --individual --batch

# Test with forced cache refresh
python -m backend.data_enrichment.test_geocoding --force-refresh
```

### Performance Benchmarking

```bash
# Benchmarking cache performance
python -m backend.data_enrichment.cli benchmark-cache

# Benchmarking database operations
python -m backend.data_enrichment.cli benchmark-db-ops

# Profiling full enrichment pipeline
python -m backend.data_enrichment.cli profile-enrichment --property-id <UUID>
```

### Troubleshooting

Common issues and solutions:

1. **API Connection Issues**:
   - Check API keys in environment variables
   - Verify network connectivity
   - Check API rate limits and quotas

2. **Database Connection Failures**:
   - Verify Supabase URL and API key
   - Check database permissions
   - Ensure proper table schema exists

3. **MCP Server Problems**:
   - Verify MCP server is running
   - Check MCP server logs
   - Test direct connection to MCP endpoint

4. **Cache Corruption**:
   - Clear corrupted cache with `python -m backend.data_enrichment.cli clear-cache`
   - Check disk space
   - Verify file permissions on cache directory

## Architecture

The data enrichment module is organized into several key components:

```
data_enrichment/
├── __init__.py
├── geocoding_service.py       # Advanced geocoding service with multiple providers
├── enrichment_agent.py        # Basic data enrichment agent
├── database_extensions.py     # Database operations for enrichment
├── mcp_client.py              # Client for interacting with MCP server
├── property_researcher.py     # Main orchestrator for deep research
├── cache_manager.py           # Caching system for research results
├── config.py                  # Configuration settings
├── cli.py                     # Command-line interface
├── scheduled_tasks.py         # Scheduled tasks for enrichment
├── test_geocoding.py          # Test script for geocoding functionality
├── research_enrichers/        # Domain-specific research modules
│   ├── __init__.py
│   ├── investment_metrics.py  # Financial and investment analysis
│   ├── market_analyzer.py     # Market conditions and trends
│   ├── property_profiler.py   # Detailed property information
│   └── risk_assessor.py       # Risk and blindspot analysis
└── README.md                  # This file
```

## Installation

1. Install the required dependencies:

```bash
pip install -r requirements.txt
```

2. Set up environment variables:

```
# Basic Enrichment
GOOGLE_PLACES_API_KEY=your_google_places_api_key
MAPBOX_ACCESS_TOKEN=your_mapbox_access_token
WALKSCORE_API_KEY=your_walkscore_api_key
NOMINATIM_USER_AGENT="AcquireApartments/1.0 (acquire-apartments.com; contact@acquire-apartments.com)"

# Deep Research APIs
OPENAI_API_KEY=your_openai_api_key
ANTHROPIC_API_KEY=your_anthropic_api_key
FMP_API_KEY=your_fmp_api_key
FRED_API_KEY=your_fred_api_key
POLYGON_API_KEY=your_polygon_api_key
ALPHA_VANTAGE_API_KEY=your_alpha_vantage_api_key
SEC_API_KEY=your_sec_api_key

# MCP Configuration
DEEP_RESEARCH_MCP_URL=http://localhost:6020/sse
```

3. Set up the MCP server:

Follow the instructions in the [Microsoft Semantic Workbench repository](https://github.com/microsoft/semanticworkbench/tree/HEAD/mcp-servers/mcp-server-open-deep-research) to set up the open-deep-research MCP server.

## Usage

### Basic Data Enrichment

```python
from backend.data_enrichment.geocoding_service import GeocodingService
from backend.data_enrichment.enrichment_agent import enrichment_agent
from backend.data_enrichment.cache_manager import ResearchCacheManager

# Initialize geocoding service with caching
cache_manager = ResearchCacheManager()
geocoding_service = GeocodingService(cache_manager=cache_manager)

# Geocode a property (async)
import asyncio

async def geocode_example():
    # Geocode a single address with default provider
    result = await geocoding_service.geocode_address(
        address="1234 Main St", 
        city="Austin", 
        state="TX"
    )
    print(f"Coordinates: {result['latitude']}, {result['longitude']}")
    
    # Geocode with specific provider
    result = await geocoding_service.geocode_address(
        address="1234 Main St", 
        city="Austin", 
        state="TX",
        provider="nominatim"  # Use OpenStreetMap's Nominatim service
    )
    
    # Batch geocode multiple properties
    properties = [
        {"id": "prop1", "address": "1234 Main St", "city": "Austin", "state": "TX"},
        {"id": "prop2", "address": "5678 Elm St", "city": "Austin", "state": "TX"}
    ]
    batch_results = await geocoding_service.batch_geocode(
        properties=properties,
        concurrency=2
    )

# Run the async example
asyncio.run(geocode_example())

# Enrich a property (using the enrichment agent)
property_data = {
    "name": "Riverside Apartments",
    "address": "1234 Riverside Dr",
    "city": "Austin",
    "state": "TX"
}
enriched_property = enrichment_agent.enrich_property(property_data)
```

### Deep Property Research

```python
from backend.data_enrichment.property_researcher import PropertyResearcher

# Initialize the researcher
researcher = PropertyResearcher()

# Research a property (async)
import asyncio

async def research_example():
    property_data = {
        "name": "Riverside Apartments",
        "address": "1234 Riverside Dr",
        "city": "Austin",
        "state": "TX",
        "units": 120,
        "year_built": 1995,
        "description": "120-unit multifamily property built in 1995 with pool and fitness center."
    }
    
    # Geocode the property to get precise coordinates
    geocoded_property = await researcher.geocode_property(property_data)
    print(f"Coordinates: {geocoded_property.get('latitude')}, {geocoded_property.get('longitude')}")
    
    # Conduct research with different depth levels
    basic_result = await researcher.research_property(
        property_data=geocoded_property,  # Using the geocoded property data
        research_depth="basic"
    )
    
    comprehensive_result = await researcher.research_property(
        property_data=property_data,
        research_depth="comprehensive"
    )
    
    # Print executive summary
    print(comprehensive_result["executive_summary"])
    
    # Access specific analysis modules
    investment_metrics = comprehensive_result["modules"]["investment_potential"]
    ownership_history = comprehensive_result["modules"]["property_details"]["ownership_history"]
    
    # Batch geocode multiple properties
    another_property = {
        "name": "Downtown Lofts",
        "address": "500 Congress Ave",
        "city": "Austin",
        "state": "TX"
    }
    properties = [property_data, another_property]
    
    geocoding_results = await researcher.batch_geocode_properties(
        properties=properties,
        concurrency=2
    )
    geocoded_properties = geocoding_results["properties"]
    
    # Batch research multiple properties
    batch_results = await researcher.batch_research_properties(
        properties=geocoded_properties,
        research_depth="standard",
        concurrency=2
    )

# Run the async example
asyncio.run(research_example())
```

### Command-Line Interface

```bash
# Geocode a property from the database
python -m backend.data_enrichment.cli geocode --property-id 123e4567-e89b-12d3-a456-426614174000 --provider google

# Batch geocode properties from the database
python -m backend.data_enrichment.cli batch-geocode --limit 20 --concurrency 3

# Research a property from the database
python -m backend.data_enrichment.cli research --property-id 123e4567-e89b-12d3-a456-426614174000 --depth comprehensive

# Research a property from a file
python -m backend.data_enrichment.cli research --input-file property.json --output-file research_results.json --depth standard

# Batch research properties from the database
python -m backend.data_enrichment.cli batch-research --limit 10 --concurrency 3 --depth standard

# Run scheduled research tasks
python -m backend.data_enrichment.cli run-scheduled-tasks
```

## Research Depth Levels

The system supports four levels of research depth:

1. **Basic**: Quick analysis using readily available data (1-2 minutes)
2. **Standard**: Standard analysis with some API enrichment (2-5 minutes)
3. **Comprehensive**: Full API enrichment and MCP research (5-15 minutes)
4. **Exhaustive**: Maximum depth analysis with all data sources (15-30 minutes)

## MCP Integration

The system leverages Microsoft's open-deep-research MCP server to provide sophisticated property analysis capabilities:

- For deeper property details beyond what direct APIs can provide
- For complex investment analysis like LBO modeling
- For identifying non-obvious risks and blindspots
- For generating comprehensive executive summaries

The MCP server is used selectively based on the research depth level, with basic research running without MCP dependency for faster results.

## Caching System

Research results are cached to minimize redundant API calls and computation:

- Memory cache for fast access to recent queries
- Disk cache for persistent storage
- Different TTLs (Time To Live) based on data type:
  - Property details: 30 days
  - Investment metrics: 7 days
  - Market conditions: 7 days
  - Risk assessments: 90 days

## Database Integration

The system can save research results back to the database:

- Store in Supabase `property_research` table
- Create relationships in Neo4j between properties and research results
- Automatically update research when properties change

## Scheduled Tasks

The module includes Celery tasks for scheduled research:

- `research_new_properties_task`: Research new properties added in the last 24 hours
- `refresh_outdated_research_task`: Refresh research for properties with outdated results
- `deep_research_high_priority_task`: Run comprehensive research on high-priority properties

## Logging

The module logs detailed information about the research process:

- Research status and timing
- API call successes and failures
- MCP server interactions
- Cache hits and misses

Logs are written to `data_enrichment.log` and `deep_research.log`.

## Configuration

The module can be configured through the `config.py` file and environment variables:

- MCP server settings
- API configurations
- Research depth parameters
- Caching settings
- Database operations

### Cost Control Settings

To manage token usage and API costs, several parameters can be adjusted:

1. **CLI Batch Size Controls**:
   ```bash
   python3 -m backend.data_enrichment.cli batch-research --limit 10 --depth basic --concurrency 2
   ```
   - `--limit`: Controls maximum properties processed (default: 10)
   - `--concurrency`: Limits parallel operations (default: 3)
   - `--depth`: Controls API usage intensity (minimal, basic, standard, full)

2. **Scheduled Task Volume**:
   - Edit batch sizes in `scheduled_tasks.py` (defaults: 20-50 properties)
   - Modify concurrency settings (currently 2-3 depending on task type)
   - Adjust task scheduling frequency

3. **Database Batch Settings**:
   - `DB_CONFIG["supabase"]["batch_size"]` in `config.py` controls database update batch size
   - Default value is 50 items per batch

4. **API Rate Limiting**:
   - API usage is controlled through rate limits defined in `API_CONFIG`
   - Research depth levels determine API call frequency and volume

Start with small batches (5-10 properties) to monitor costs before scaling up to larger volumes.

## Error Handling

The system implements comprehensive error handling:

- Graceful fallbacks when APIs fail
- Automatic retries with exponential backoff
- Partial results when some components fail
- Detailed error reporting 