# Search & Filter Capabilities

This document outlines the available search and filter parameters for the frontend to implement when querying property listings.

## Overview

The Acquire Apartments platform provides comprehensive search and filtering capabilities to help users quickly find properties that match their specific criteria. These filters can be applied via the API and should be implemented in the frontend user interface.

## Available Filters

### Basic Filters

| Filter | Type | Description | API Parameter |
|--------|------|-------------|--------------|
| Status | Enum | Filter by property status | `status` |
| Price Range | Number | Minimum and maximum price | `min_price`, `max_price` |
| Units Range | Number | Minimum and maximum number of units | `min_units`, `max_units` |
| Year Built Range | Number | Minimum and maximum year built | `year_built_min`, `year_built_max` |
| Cap Rate Range | Number | Minimum and maximum capitalization rate | `cap_rate_min`, `cap_rate_max` |
| Location | Text | Filter by city, state, or ZIP code | `city`, `state`, `zip` |
| Text Search | Text | Search across name, address, description | `search` |

### Advanced Filters

| Filter | Type | Description | API Parameter |
|--------|------|-------------|--------------|
| Property Type | Enum | Filter by property type (multifamily, mixed-use, etc.) | `property_type` |
| Brokerage | Text | Filter by brokerage company | `brokerage` |
| Broker | Text | Filter by specific broker | `broker` |
| Amenities | Array | Filter by available amenities | `amenities` |
| Radius Search | Geo | Properties within radius of lat/lng | `lat`, `lng`, `radius` |
| Map Bounds | Geo | Properties within map viewport | `bounds[north]`, `bounds[south]`, `bounds[east]`, `bounds[west]` |
| Date Listed | Date | Filter by listing date range | `listed_after`, `listed_before` |
| NOI Range | Number | Minimum and maximum net operating income | `min_noi`, `max_noi` |

## API Query Structure

### Basic Query Example

```
GET /api/v1/properties?status=available&min_price=5000000&max_price=15000000&min_units=50&city=Austin&state=TX
```

### Advanced Query Example

```
GET /api/v1/properties?bounds[north]=30.4&bounds[south]=30.2&bounds[east]=-97.6&bounds[west]=-97.8&property_type=MULTIFAMILY&cap_rate_min=4.5
```

## Pagination

All property list queries support pagination:

| Parameter | Type | Description | Default |
|-----------|------|-------------|---------|
| page | Number | Page number | 1 |
| limit | Number | Items per page | 20 |

Example:
```
GET /api/v1/properties?page=2&limit=50
```

Response includes pagination metadata:
```json
{
  "items": [ /* property objects */ ],
  "pagination": {
    "total": 543,
    "page": 2,
    "limit": 50,
    "pages": 11
  }
}
```

## Sorting

Property results can be sorted using the following parameters:

| Parameter | Description |
|-----------|-------------|
| `sort_by=price&sort_dir=asc` | Price (low to high) |
| `sort_by=price&sort_dir=desc` | Price (high to low) |
| `sort_by=date&sort_dir=desc` | Newest first |
| `sort_by=units&sort_dir=desc` | Most units first |
| `sort_by=year_built&sort_dir=desc` | Newest construction first |
| `sort_by=cap_rate&sort_dir=desc` | Highest cap rate first |

## Implementation Guidelines

### Frontend Filter Components

The frontend should implement the following filter components:

1. **Filter Bar**: For common filters (status, price range, units)
2. **Advanced Filter Panel**: For less common filters (expandable)
3. **Map-Based Filtering**: Drawing tools or viewport-based filtering
4. **Search Box**: For text-based searching
5. **Sort Dropdown**: For changing result order

### State Management

Filter state should be:
- Stored in URL parameters for shareable filtered views
- Synchronized with browser history
- Persisted in local storage for returning users
- Saved to user account for logged-in users

### Performance Considerations

- Debounce filter changes (especially ranges)
- Implement progressive loading for map markers
- Cache filter results when appropriate
- Use skeleton loaders during filter operations

### UI/UX Recommendations

1. **Visual Indicators**: Show active filters with badges
2. **Clear Filters**: Provide a "clear all" button
3. **Save Filters**: Allow users to save filter combinations
4. **Filter Insights**: Show counts of properties matching filters
5. **Smart Defaults**: Set sensible default filter values based on market

## Available Property Status Values

- `available` - Currently on the market
- `pending` - Under contract but not yet closed
- `sold` - Transaction completed
- `off_market` - Temporarily not for sale
- `expired` - Listing is no longer active

## Available Property Types

- `MULTIFAMILY` - Apartment buildings
- `MIXED_USE` - Combined residential and commercial
- `STUDENT_HOUSING` - Designed for student tenants
- `SENIOR_LIVING` - Age-restricted communities
- `AFFORDABLE` - Income-restricted housing
- `LUXURY` - High-end apartments

## Amenity Filter Values

- `pool`
- `fitness_center`
- `covered_parking`
- `pet_friendly`
- `washer_dryer`
- `clubhouse`
- `business_center`
- `elevator`
- `playground`
- `gated`

## Example Implementation

```javascript
// Filter state in React component
const [filters, setFilters] = useState({
  status: 'available',
  min_price: 5000000,
  max_price: 15000000,
  min_units: 50,
  max_units: null,
  city: 'Austin',
  state: 'TX',
  property_type: 'MULTIFAMILY',
  sort_by: 'date',
  sort_dir: 'desc',
  page: 1,
  limit: 20
});

// Function to update filters
const updateFilter = (key, value) => {
  setFilters(prev => ({
    ...prev,
    [key]: value,
    // Reset to page 1 when filters change
    page: 1
  }));
};

// Function to build query string
const buildQueryString = (filters) => {
  const queryParams = new URLSearchParams();
  
  Object.entries(filters).forEach(([key, value]) => {
    if (value !== null && value !== undefined && value !== '') {
      queryParams.append(key, value);
    }
  });
  
  return queryParams.toString();
};

// Function to fetch filtered properties
const fetchProperties = async () => {
  const queryString = buildQueryString(filters);
  const response = await fetch(`/api/v1/properties?${queryString}`);
  return response.json();
};
```