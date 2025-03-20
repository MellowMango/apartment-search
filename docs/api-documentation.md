# API Documentation for Frontend Integration

## Overview

This document provides comprehensive information about the backend API endpoints, data structures, and authentication flows required for frontend development. This will serve as a foundation for implementing the map view, search/filter functionality, and real-time updates.

## Base URL

- Development: `http://localhost:8000/api/v1`
- Production: `https://acquire-backend.herokuapp.com/api/v1`

## Authentication

All protected endpoints require a valid JWT token in the `Authorization` header.

### Auth Endpoints

#### Register User

```
POST /auth/register
```

Request:
```json
{
  "email": "user@example.com",
  "password": "securepassword123",
  "name": "John Doe"
}
```

Response:
```json
{
  "user": {
    "id": "123e4567-e89b-12d3-a456-426614174000",
    "email": "user@example.com",
    "name": "John Doe",
    "created_at": "2023-01-01T00:00:00Z"
  },
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

#### Login

```
POST /auth/login
```

Request:
```json
{
  "email": "user@example.com",
  "password": "securepassword123"
}
```

Response:
```json
{
  "user": {
    "id": "123e4567-e89b-12d3-a456-426614174000",
    "email": "user@example.com",
    "name": "John Doe",
    "created_at": "2023-01-01T00:00:00Z"
  },
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

#### Reset Password

```
POST /auth/reset-password
```

Request:
```json
{
  "email": "user@example.com"
}
```

Response:
```json
{
  "message": "Password reset email sent"
}
```

## Property Endpoints

### Get All Properties

```
GET /properties
```

Query Parameters:
- `page` (default: 1): Page number
- `limit` (default: 50): Items per page
- `status` (optional): Filter by status (available, pending, sold)
- `min_price` (optional): Minimum price
- `max_price` (optional): Maximum price
- `min_units` (optional): Minimum number of units
- `max_units` (optional): Maximum number of units
- `city` (optional): Filter by city
- `state` (optional): Filter by state
- `zip` (optional): Filter by ZIP code
- `year_built_min` (optional): Minimum year built
- `year_built_max` (optional): Maximum year built
- `cap_rate_min` (optional): Minimum cap rate
- `cap_rate_max` (optional): Maximum cap rate
- `search` (optional): Text search (searches name, address, description)

Response:
```json
{
  "items": [
    {
      "id": "123e4567-e89b-12d3-a456-426614174000",
      "name": "Riverside Apartments",
      "address": "123 Riverside Dr",
      "city": "Austin",
      "state": "TX",
      "zip": "78701",
      "latitude": 30.2672,
      "longitude": -97.7431,
      "price": 10000000,
      "units": 100,
      "year_built": 1995,
      "status": "available",
      "cap_rate": 5.2,
      "image_url": "https://example.com/image.jpg",
      "created_at": "2023-01-01T00:00:00Z",
      "updated_at": "2023-01-01T00:00:00Z"
    },
    // Additional properties...
  ],
  "pagination": {
    "total": 543,
    "page": 1,
    "limit": 50,
    "pages": 11
  }
}
```

### Get Property by ID

```
GET /properties/{property_id}
```

Response:
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "name": "Riverside Apartments",
  "address": "123 Riverside Dr",
  "city": "Austin",
  "state": "TX",
  "zip": "78701",
  "latitude": 30.2672,
  "longitude": -97.7431,
  "price": 10000000,
  "units": 100,
  "year_built": 1995,
  "status": "available",
  "description": "Luxurious apartment complex with riverside views...",
  "cap_rate": 5.2,
  "noi": 520000,
  "price_per_unit": 100000,
  "broker": {
    "id": "123e4567-e89b-12d3-a456-426614174001",
    "name": "Jane Smith",
    "email": "jane@brokerage.com",
    "phone": "512-555-1234",
    "brokerage": {
      "id": "123e4567-e89b-12d3-a456-426614174002",
      "name": "ABC Brokerage",
      "website": "https://abcbrokerage.com"
    }
  },
  "images": [
    "https://example.com/image1.jpg",
    "https://example.com/image2.jpg"
  ],
  "amenities": [
    "Pool",
    "Fitness Center",
    "Covered Parking"
  ],
  "research": {
    "neighborhood_stats": {
      "walk_score": 85,
      "transit_score": 72,
      "bike_score": 90
    },
    "market_trends": {
      "vacancy_rate": 4.5,
      "rent_growth": 3.2,
      "avg_rent": 1450
    }
  },
  "created_at": "2023-01-01T00:00:00Z",
  "updated_at": "2023-01-01T00:00:00Z"
}
```

### Get Similar Properties

```
GET /properties/{property_id}/similar
```

Query Parameters:
- `limit` (default: 5): Number of similar properties to return

Response:
```json
{
  "items": [
    {
      "id": "123e4567-e89b-12d3-a456-426614174003",
      "name": "Downtown Lofts",
      "address": "456 Main St",
      "city": "Austin",
      "state": "TX",
      "latitude": 30.2742,
      "longitude": -97.7400,
      "price": 9500000,
      "units": 95,
      "year_built": 1998,
      "status": "available",
      "similarity_score": 0.92
    },
    // Additional similar properties...
  ]
}
```

## Broker Endpoints

### Get All Brokers

```
GET /brokers
```

Query Parameters:
- `page` (default: 1): Page number
- `limit` (default: 50): Items per page
- `search` (optional): Text search (searches name, email, brokerage)

Response:
```json
{
  "items": [
    {
      "id": "123e4567-e89b-12d3-a456-426614174001",
      "name": "Jane Smith",
      "email": "jane@brokerage.com",
      "phone": "512-555-1234",
      "brokerage": {
        "id": "123e4567-e89b-12d3-a456-426614174002",
        "name": "ABC Brokerage"
      },
      "active_listing_count": 12
    },
    // Additional brokers...
  ],
  "pagination": {
    "total": 78,
    "page": 1,
    "limit": 50,
    "pages": 2
  }
}
```

### Get Broker by ID

```
GET /brokers/{broker_id}
```

Response:
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174001",
  "name": "Jane Smith",
  "email": "jane@brokerage.com",
  "phone": "512-555-1234",
  "bio": "Jane has over 15 years of experience in multifamily real estate...",
  "photo_url": "https://example.com/jane.jpg",
  "brokerage": {
    "id": "123e4567-e89b-12d3-a456-426614174002",
    "name": "ABC Brokerage",
    "website": "https://abcbrokerage.com",
    "logo_url": "https://example.com/abclogo.png"
  },
  "active_listings": [
    {
      "id": "123e4567-e89b-12d3-a456-426614174000",
      "name": "Riverside Apartments",
      "address": "123 Riverside Dr",
      "city": "Austin",
      "state": "TX",
      "price": 10000000,
      "units": 100,
      "status": "available"
    },
    // Additional listings...
  ]
}
```

## User Profile Endpoints

### Get Current User Profile

```
GET /users/me
```

Response:
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "email": "user@example.com",
  "name": "John Doe",
  "created_at": "2023-01-01T00:00:00Z",
  "subscription": {
    "plan": "premium",
    "status": "active",
    "expires_at": "2024-01-01T00:00:00Z"
  },
  "saved_properties": [
    {
      "id": "123e4567-e89b-12d3-a456-426614174000",
      "name": "Riverside Apartments",
      "address": "123 Riverside Dr",
      "saved_at": "2023-01-15T00:00:00Z"
    },
    // Additional saved properties...
  ]
}
```

### Update User Profile

```
PATCH /users/me
```

Request:
```json
{
  "name": "John Smith",
  "email": "john.smith@example.com"
}
```

Response:
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "email": "john.smith@example.com",
  "name": "John Smith",
  "created_at": "2023-01-01T00:00:00Z",
  "updated_at": "2023-02-01T00:00:00Z"
}
```

### Save Property

```
POST /users/me/saved-properties
```

Request:
```json
{
  "property_id": "123e4567-e89b-12d3-a456-426614174000"
}
```

Response:
```json
{
  "message": "Property saved successfully",
  "saved_at": "2023-02-01T00:00:00Z"
}
```

### Remove Saved Property

```
DELETE /users/me/saved-properties/{property_id}
```

Response:
```json
{
  "message": "Property removed from saved list"
}
```

## Real-Time Updates

Real-time property updates are delivered via Socket.IO. Connect to the Socket.IO server at:

```
ws://localhost:8000/socket.io
```

### Events

#### Property Updated

This event is emitted when a property is updated in the database.

```json
{
  "event": "property-updated",
  "data": {
    "property_id": "123e4567-e89b-12d3-a456-426614174000",
    "changes": {
      "status": {
        "old": "available",
        "new": "pending"
      },
      "price": {
        "old": 10000000,
        "new": 9800000
      }
    },
    "updated_at": "2023-02-01T00:00:00Z"
  }
}
```

#### New Property Listed

This event is emitted when a new property is added to the database.

```json
{
  "event": "property-created",
  "data": {
    "property_id": "123e4567-e89b-12d3-a456-426614174005",
    "name": "Oak View Apartments",
    "city": "Austin",
    "state": "TX",
    "price": 12500000,
    "units": 120,
    "created_at": "2023-02-01T00:00:00Z"
  }
}
```

## Search & Filter Capabilities

The frontend should implement the following search and filter capabilities using the query parameters supported by the `/properties` endpoint:

1. **Text Search**: Allow users to search by property name, address, or description using the `search` parameter
2. **Status Filter**: Filter properties by status (available, pending, sold)
3. **Price Range**: Filter properties by minimum and maximum price
4. **Units Range**: Filter by minimum and maximum number of units
5. **Location Filters**: Filter by city, state, or ZIP code
6. **Year Built Range**: Filter by minimum and maximum year built
7. **Cap Rate Range**: Filter by minimum and maximum cap rate

The frontend should also implement:

1. **Map-Based Filtering**: Allow users to filter properties by drawing a polygon on the map
2. **Sorting Options**: Sort by price (high to low, low to high), newest first, units (high to low), year built (newest first)
3. **Saved Filters**: Allow users to save and quickly apply frequently used filter combinations

## Data Structure For Map Integration

When implementing the map view, the frontend should use the following data structure for each property marker:

```typescript
interface PropertyMarker {
  id: string;
  name: string;
  latitude: number;
  longitude: number;
  price: number;
  units: number;
  status: "available" | "pending" | "sold";
  address: string;
  city: string;
  state: string;
  imageUrl?: string;
  capRate?: number;
}
```

For the property detail view when a marker is clicked:

```typescript
interface PropertyDetail extends PropertyMarker {
  description: string;
  yearBuilt: number;
  pricePerUnit: number;
  noi?: number;
  broker: {
    name: string;
    email: string;
    phone: string;
    brokerage: string;
  };
  amenities: string[];
  images: string[];
}
```

## Implementation Recommendations

1. **State Management**: Use React Context API for global state management, especially for:
   - Current user authentication state
   - Map filter state
   - Saved properties list
   - Real-time property updates

2. **API Integration**:
   - Create a custom hook for each API endpoint
   - Implement proper loading, error, and success states
   - Use React Query for data fetching and caching

3. **Map Implementation**:
   - Use react-leaflet for the map component
   - Implement custom markers for different property statuses
   - Use clustering for areas with many properties
   - Implement a sidebar that shows properties in the current map view

4. **Real-Time Updates**:
   - Use socket.io-client to connect to the WebSocket server
   - Update the global state when real-time events are received
   - Show notifications for important updates

5. **Authentication**:
   - Implement a protected route component for authenticated pages
   - Store JWT token in localStorage or cookies
   - Auto-refresh tokens before they expire
   - Handle unauthorized responses properly

## Error Handling

All API endpoints follow a consistent error response format:

```json
{
  "error": true,
  "message": "Detailed error message",
  "code": "ERROR_CODE"
}
```

Common error codes:
- `UNAUTHORIZED`: User is not authenticated
- `FORBIDDEN`: User doesn't have permission for the requested resource
- `NOT_FOUND`: Requested resource was not found
- `VALIDATION_ERROR`: Invalid request parameters
- `INTERNAL_ERROR`: Server error

The frontend should handle these errors appropriately and display user-friendly error messages.