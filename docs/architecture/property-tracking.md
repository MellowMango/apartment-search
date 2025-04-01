# Property Tracking Implementation

## Overview

The property tracking feature enhances our ability to trace the origins of property data throughout the system. This documentation covers the implementation of property tracking for collection results (task P1-33).

## Purpose

Property tracking helps us:

1. Identify which collector discovered each property
2. Track when a property was first collected and by which source
3. Maintain data lineage and provenance
4. Enable more sophisticated analysis of data sources
5. Support data quality monitoring and debugging

## Implementation Details

### Enhanced Collection Result

The `CollectionResult` class has been enhanced with the following tracking information:

- `source_id`: Identifier for the data source (e.g., broker name)
- `source_type`: Type of source (e.g., "scraper", "api", "upload")
- `collection_context`: Additional contextual information about the collection

A new `get_tracking_data()` method returns a standardized dictionary of tracking information that can be used when storing properties:

```python
{
    "collection_id": "a-uuid-string",
    "source_id": "acrmultifamily",
    "source_type": "scraper",
    "collected_at": "2025-03-27T12:34:56",
    "collection_context": {
        "collector_type": "ACRMultifamilyCollector",
        "scraper_type": "ACRMultifamilyScraper",
        "parameters": {...},
        "property_count": 10,
        "time_taken_seconds": 5.23,
        "base_url": "https://example.com"
    }
}
```

### Updated BaseScraperCollector

The `BaseScraperCollector.collect_data()` method now populates this tracking information automatically, including:

- Setting the appropriate `source_id` and `source_type`
- Collecting context information like scraper type, parameters, and count
- Adding broker-specific details when available

### Enhanced Property Storage

The `PropertyStorage` class has been extended with:

1. `store_property_with_tracking()`: Stores a property with its collection tracking information
2. `query_by_source()`: Queries properties by their source identifier
3. `query_by_collection()`: Queries properties by their collection identifier

When storing a property with tracking, the following occurs:

1. Tracking data is embedded in the property's metadata as `collection_tracking`
2. Direct tracking fields are added to the property for efficient querying:
   - `source_id`: ID of the data source
   - `collection_id`: ID of the collection operation
   - `source_type`: Type of data source
   - `collected_at`: When the property was collected

## How to Use Property Tracking

### Collecting Properties with Tracking

When using a `DataSourceCollector` to collect properties, tracking information is automatically included in the `CollectionResult`:

```python
collector = ACRMultifamilyCollector(scraper)
collection_result = await collector.collect_data("acrmultifamily", params)
```

### Storing Properties with Tracking

When storing properties from a collection, use `store_property_with_tracking()`:

```python
# Get tracking data from collection result
tracking_data = collection_result.get_tracking_data()

# Store each property with tracking
for property_data in collection_result.data.get("properties", []):
    result = await property_storage.store_property_with_tracking(
        property_data, tracking_data
    )
```

### Querying Properties by Source

To find all properties from a specific source:

```python
# Get properties from ACR Multifamily
query_result = await property_storage.query_by_source(
    "acrmultifamily",
    PaginationParams(page=1, page_size=20)
)

# Access the properties
properties = query_result.items
```

### Querying Properties by Collection

To find all properties from a specific collection operation:

```python
# Get properties from a specific collection
query_result = await property_storage.query_by_collection(
    collection_id,
    PaginationParams(page=1, page_size=20)
)
```

## Database Schema Changes

The property tracking implementation requires the following fields in the properties table:

- `source_id`: VARCHAR - ID of the data source
- `collection_id`: VARCHAR - ID of the collection operation
- `source_type`: VARCHAR - Type of data source
- `collected_at`: TIMESTAMP - When the property was collected
- `metadata`: JSONB - Contains the full tracking information

A database migration script will be created separately to add these fields if they don't already exist.