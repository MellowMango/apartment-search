# API Response Format

This document outlines the standardized API response format used across all endpoints in the Acquire API.

## Standard Response Structure

All API responses follow a consistent structure:

```json
{
  "success": true|false,
  "data": <response data>,
  "message": "Human-readable message",
  "errors": [
    {
      "code": "error_code",
      "message": "Error message",
      "field": "field_name",
      "details": { <additional details> }
    }
  ],
  "meta": {
    "timestamp": "2025-03-28T12:34:56.789Z",
    "request_id": "unique-request-id",
    "pagination": {
      "page": 1,
      "page_size": 10,
      "total_items": 100,
      "total_pages": 10,
      "has_next": true,
      "has_prev": false
    },
    "process_time_ms": 123.45
  }
}
```

### Fields

- **success**: Boolean indicating whether the request was successful
- **data**: The main response payload (null if error)
- **message**: Human-readable message describing the result
- **errors**: Array of error details (only present if success is false)
- **meta**: Metadata about the request/response

## Response Types

### Success Response

A successful operation returns:

```json
{
  "success": true,
  "data": { ... },
  "message": "Operation completed successfully",
  "meta": { ... }
}
```

### Error Response

An error returns:

```json
{
  "success": false,
  "message": "Operation failed",
  "errors": [
    {
      "code": "validation_error",
      "message": "Invalid input",
      "field": "email",
      "details": { "pattern": "^[^@]+@[^@]+\\.[^@]+$" }
    }
  ],
  "meta": { ... }
}
```

### Paginated Response

Responses with multiple items include pagination metadata:

```json
{
  "success": true,
  "data": [ ... ],
  "message": "Items retrieved successfully",
  "meta": {
    "pagination": {
      "page": 2,
      "page_size": 10,
      "total_items": 87,
      "total_pages": 9,
      "has_next": true,
      "has_prev": true
    },
    ...
  }
}
```

## HTTP Status Codes

The API uses standard HTTP status codes:

- **200 OK**: Successful operation
- **201 Created**: Resource successfully created
- **204 No Content**: Successful operation with no response body
- **400 Bad Request**: Invalid input, parameter validation error
- **401 Unauthorized**: Authentication failure
- **403 Forbidden**: Permission denied
- **404 Not Found**: Resource not found
- **422 Unprocessable Entity**: Validation error (semantically invalid)
- **429 Too Many Requests**: Rate limit exceeded
- **500 Internal Server Error**: Server error

## Error Codes

Common error codes include:

| Code | Description |
|------|-------------|
| `validation_error` | Input validation failed |
| `not_found` | Resource not found |
| `authentication_error` | Authentication failed |
| `permission_error` | Permission denied |
| `conflict_error` | Resource conflict |
| `rate_limit_exceeded` | Rate limit exceeded |
| `bad_request` | General bad request |
| `server_error` | Server error |
| `storage_error` | Database/storage error |
| `dependency_error` | External service error |
| `geocoding_error` | Geocoding service error |

## Response Headers

All responses include these headers:

- `X-Correlation-ID`: Unique identifier for the request (for tracking)
- `X-Request-ID`: Same as correlation ID (for compatibility)

Rate-limited endpoints also include:

- `X-RateLimit-Limit`: Maximum requests per time window
- `X-RateLimit-Remaining`: Remaining requests in current window
- `X-RateLimit-Reset`: Unix timestamp when the rate limit resets