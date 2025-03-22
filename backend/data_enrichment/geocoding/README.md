# Geocoding System Documentation

## Overview

The geocoding system is responsible for converting address information into geographic coordinates (latitude and longitude) for all properties in the database. It provides:

- Multi-provider support (Google, Bing, Mapbox, etc.)
- Caching for performance and cost efficiency
- Batch processing capabilities
- Automated validation and monitoring
- Visualization of geocoding metrics

## Key Components

### Core Components

1. **GeocodingService** (`backend/data_enrichment/geocoding_service.py`)
   - Main service that handles geocoding address data
   - Supports multiple geocoding providers
   - Implements caching to reduce API costs
   - Provides batch geocoding functionality

2. **PropertyResearcher** (`backend/data_enrichment/property_researcher.py`)
   - Orchestrates property research including geocoding
   - Validates property data before enrichment
   - Caches research results to avoid duplicate work

3. **RetryManager** (`backend/data_enrichment/retry_manager.py`)
   - Handles temporary failures with exponential backoff
   - Provides robust error handling for API calls
   - Customizable retry conditions based on exception types

### Automation Scripts

1. **Batch Geocoding Script** (`backend/scripts/run_geocode_batch.py`)
   - Command-line tool for batch geocoding operations
   - Fixes properties with missing or invalid coordinates
   - Handles duplicate research entries

2. **Scheduled Geocoding Worker** (`backend/app/workers/scheduled_geocoding.py`)
   - Background worker for periodic geocoding tasks
   - Multiple modes for different geocoding operations
   - Integrated with crontab for automation

3. **Geocoding Monitor** (`backend/app/workers/geocoding_monitor.py`)
   - Monitors geocoding quality and accuracy
   - Generates alerts for detected issues
   - Creates periodic reports on geocoding health

4. **Visualization Script** (`backend/scripts/visualize_geocoding_metrics.py`)
   - Creates visual charts of geocoding quality metrics
   - Tracks success rates, failure types, and other metrics
   - Generates static HTML reports

### Testing & Validation

1. **Validation Tests** (`backend/tests/geocoding/test_geocoding_validation.py`)
   - Validates geocoding accuracy
   - Detects suspicious coordinate patterns
   - Provides systematic verification of geocoded properties

2. **Integration Tests** (`backend/tests/geocoding/test_geocoding_integration.py`)
   - Tests integration with external geocoding providers
   - Verifies caching behavior
   - Ensures correct handling of various address formats

## Workflow

1. **Regular Geocoding**:
   - Hourly jobs process properties with missing coordinates
   - Properties with suspicious coordinates are repaired every 6 hours
   - Weekly comprehensive refresh of all property coordinates

2. **Monitoring and Validation**:
   - Daily monitoring checks sample of properties
   - Weekly validation tests run on Saturday mornings
   - Weekly reports and visualizations generated every Monday

3. **Maintenance**:
   - Monthly full maintenance runs
   - Fixes duplicate research entries daily
   - Ensures database integrity and high-quality geocoding

## Crontab Configuration

The crontab configuration (`backend/scripts/crontab_config.txt`) handles all scheduled tasks:

```
# Hourly: Fix missing coordinates
0 * * * * cd /path/to/your/project && python3 backend/app/workers/scheduled_geocoding.py --mode=fix_missing --limit=100

# Every 6 hours: Repair suspicious coordinates
0 */6 * * * cd /path/to/your/project && python3 backend/app/workers/scheduled_geocoding.py --mode=repair_suspicious --limit=50

# Daily at 7 AM: Quality monitoring
0 7 * * * cd /path/to/your/project && python3 backend/app/workers/geocoding_monitor.py --sample-size=150 --email="admin@your-company.com"

# Mondays at 8 AM: Weekly report generation
0 8 * * 1 cd /path/to/your/project && python3 backend/app/workers/geocoding_monitor.py --generate-report --output="weekly_geocoding_report.json"

# Mondays at 8:30 AM: Generate visualization charts
30 8 * * 1 cd /path/to/your/project && python3 backend/scripts/visualize_geocoding_metrics.py --days=30 --output-dir="/var/www/html/geocoding-metrics"

# Daily at 3 AM: Fix duplicate research entries
0 3 * * * cd /path/to/your/project && python3 backend/scripts/run_geocode_batch.py --fix-duplicates --limit=100

# Saturdays at 1 AM: Validate geocoding accuracy
0 1 * * 6 cd /path/to/your/project && python3 backend/tests/geocoding/test_geocoding_validation.py --run-validation --save-to-db

# Sundays at 2 AM: Comprehensive geocode refresh
0 2 * * 0 cd /path/to/your/project && python3 backend/app/workers/scheduled_geocoding.py --mode=refresh_all --limit=1000

# Monthly on the 1st at 3 AM: Full maintenance
0 3 1 * * cd /path/to/your/project && python3 backend/app/workers/scheduled_geocoding.py --mode=full_maintenance
```

## Best Practices

1. **Provider Failover**: Always configure multiple geocoding providers for redundancy
2. **Rate Limiting**: Respect provider rate limits through proper batching and delays
3. **Validation**: Always validate coordinates after geocoding operations
4. **Monitoring**: Regular monitoring to catch and fix issues early
5. **Logging**: Comprehensive logging for troubleshooting and auditing

## Common Issues and Solutions

| Issue | Solution |
|-------|----------|
| Missing coordinates | Run fix_missing mode of scheduled_geocoding.py |
| Suspicious coordinates | Run repair_suspicious mode to fix potentially incorrect geocodes |
| Rate limiting | Adjust batch sizes or implement longer delays between API calls |
| Incorrect matches | Improve address normalization or try different geocoding providers |
| Slow performance | Ensure proper caching and index optimization in database |

## Future Improvements

- Cross-provider validation for increased accuracy
- Machine learning for address parsing and normalization
- Real-time geocoding quality monitoring dashboard
- Integration with additional providers for specialized regions
- Self-healing system for automatic issue detection and resolution

## Metrics and KPIs

- **Success Rate**: Percentage of addresses successfully geocoded
- **Accuracy**: Deviation from known-good coordinates
- **Provider Reliability**: Success rates per provider
- **Failure Types**: Distribution of geocoding failure reasons
- **Processing Time**: Average time to geocode addresses 