# Geocoding Service

This document describes the geocoding service architecture and usage.

## Overview

The geocoding service converts property addresses to precise geographic coordinates (latitude and longitude) for map display and location-based queries. It uses multiple geocoding providers with fallback mechanisms.

## Features

- Multiple geocoding providers (Google Maps, Mapbox, Nominatim)
- Fallback between providers if the primary one fails
- Error handling and retry logic
- Caching of geocoding results
- Rate limiting to avoid API quota issues
- Transaction support with Unit of Work pattern
- Repository pattern for data access
- Metrics collection for monitoring

## Service Architecture

The geocoding service follows the repository pattern and is part of the API layer:

```
┌─────────────────────────┐
│    API Layer            │
│  ┌───────────────────┐  │
│  │  GeocodingService │  │
│  └───────────────┬───┘  │
└──────────────────┼──────┘
                   │
┌──────────────────┼──────┐
│  Storage Layer    │      │
│  ┌───────────────┴───┐  │
│  │ PropertyRepository │  │
│  └───────────────────┘  │
└─────────────────────────┘
```

## API

### Main Methods

#### Update Property Coordinates

```python
async def update_property_coordinates(self, property_id: str) -> Dict[str, Any]
```

Updates the coordinates for a property by ID and saves to the repository.

#### Batch Update Coordinates

```python
async def batch_update_coordinates(
    self, 
    property_ids: List[str],
    concurrency: int = 3
) -> Dict[str, Any]
```

Updates coordinates for multiple properties in parallel.

#### Verify Property Coordinates

```python
async def verify_property_coordinates(
    self, 
    property_id: str, 
    verified: bool = True
) -> Dict[str, Any]
```

Marks a property's coordinates as verified or unverified.

#### Geocode Address

```python
async def geocode_address(
    self, 
    address: str,
    city: str = "",
    state: str = "",
    zip_code: str = "",
    provider: Optional[str] = None,
    use_cache: bool = True
) -> Dict[str, Any]
```

Geocodes a single address to latitude and longitude coordinates.

### Provider-Specific Methods

- `_geocode_with_google`: Use Google Maps API
- `_geocode_with_mapbox`: Use Mapbox API
- `_geocode_with_nominatim`: Use Nominatim (OpenStreetMap) API

### Utility Methods

- `_format_address`: Format complete address from components
- `_generate_approximate_coordinates`: Generate approximated coordinates
- `_respect_rate_limit`: Implement rate limiting for providers
- `_extract_address_components`: Extract address parts from entity

## Usage Examples

### Updating a Property's Coordinates

```python
# Get an instance of the geocoding service
geocoding_service = GeocodingService()

try:
    # Update coordinates for a specific property
    updated_property = await geocoding_service.update_property_coordinates("property-123")
    
    print(f"Updated coordinates: {updated_property['latitude']}, {updated_property['longitude']}")
    
except NotFoundException as e:
    print(f"Property not found: {e.message}")
    
except GeocodingError as e:
    print(f"Geocoding error: {e.message}")
    
except StorageException as e:
    print(f"Storage error: {e.message}")
```

### Batch Geocoding

```python
# Get geocoding service
geocoding_service = GeocodingService()

# List of property IDs to update
property_ids = ["prop-1", "prop-2", "prop-3", "prop-4", "prop-5"]

# Update coordinates for all properties with concurrency of 3
results = await geocoding_service.batch_update_coordinates(
    property_ids=property_ids,
    concurrency=3
)

# Display results
print(f"Success rate: {results['stats']['success_rate']}%")
print(f"Successful: {results['stats']['success']}")
print(f"Errors: {results['stats']['errors']}")
print(f"Not found: {results['stats']['not_found']}")
```

### Direct Geocoding

```python
# Get geocoding service
geocoding_service = GeocodingService()

# Geocode an address
coords = await geocoding_service.geocode_address(
    address="1600 Amphitheatre Parkway",
    city="Mountain View",
    state="CA",
    zip_code="94043"
)

print(f"Latitude: {coords['latitude']}")
print(f"Longitude: {coords['longitude']}")
print(f"Provider: {coords['geocoding_provider']}")
```

## Error Handling

The service uses specific exception types:

- `NotFoundException`: Property not found
- `StorageException`: Error storing data
- `GeocodingError`: Error with geocoding providers

All operations use the Unit of Work pattern for transactions, ensuring that database operations are either all committed or rolled back.

## Monitoring

The service includes monitoring:

- Request counts per provider
- Success/error rates
- Request duration
- Daily usage against limits

Access usage statistics:

```python
stats = geocoding_service.get_usage_statistics()
print(f"Provider usage: {stats['request_count']}")
print(f"Available providers: {stats['available_providers']}")
```

## Configuration

The service is configured with environment variables:

- `GOOGLE_PLACES_API_KEY`: Google Maps API key
- `MAPBOX_ACCESS_TOKEN`: Mapbox access token
- `NOMINATIM_USER_AGENT`: User agent for Nominatim API

## Fallback Strategy

The service tries geocoding providers in this order:

1. Google Maps API (most accurate, but limited quota)
2. Mapbox API (good accuracy, higher quota)
3. Nominatim API (free, but less accurate and strict rate limiting)

If all providers fail, the service generates approximate coordinates based on city and state information.