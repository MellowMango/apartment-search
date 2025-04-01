# Exception and Error Handling

This document describes the exception handling architecture in the Acquire API.

## Exception Hierarchy

The API uses a comprehensive exception hierarchy for different error scenarios. All exceptions inherit from the base `APIException` class.

```
APIException
├── ClientError
│   ├── ValidationError
│   ├── NotFoundException
│   ├── AuthenticationError
│   ├── PermissionError
│   ├── ConflictError
│   ├── RateLimitExceeded
│   └── BadRequestError
└── ServerError
    ├── StorageException
    ├── DependencyError
    ├── ConfigurationError
    ├── ServiceUnavailableError
    ├── GeocodingError
    └── DataEnrichmentError
```

## Exception Classes

### Base Exception

```python
class APIException(Exception):
    status_code: int = 500
    error_code: str = "internal_error"
    default_message: str = "An internal server error occurred"
    
    def __init__(
        self, 
        message: Optional[str] = None, 
        details: Optional[Dict[str, Any]] = None,
        field: Optional[str] = None,
        sub_errors: Optional[List[Dict[str, Any]]] = None
    ):
        # Implementation...
```

### Client Errors (4xx)

Client errors indicate problems with the client request:

- **ValidationError**: Input data fails validation
- **NotFoundException**: Requested resource not found
- **AuthenticationError**: Authentication failure
- **PermissionError**: Permission denied
- **ConflictError**: Resource conflict (e.g., duplicate)
- **RateLimitExceeded**: Rate limit exceeded
- **BadRequestError**: Generic bad request

### Server Errors (5xx)

Server errors indicate problems on the server side:

- **StorageException**: Database or storage error
- **DependencyError**: External service dependency error
- **ConfigurationError**: Application configuration error
- **ServiceUnavailableError**: Service temporarily unavailable
- **GeocodingError**: Geocoding service error
- **DataEnrichmentError**: Data enrichment error

## Exception Handling Middleware

The API includes an exception handling middleware that:

1. Catches all exceptions during request processing
2. Converts exceptions to appropriate API responses
3. Maps exceptions to HTTP status codes
4. Formats error details consistently
5. Sanitizes sensitive information in error messages
6. Logs exceptions for monitoring

## Error Response Format

When an exception occurs, the middleware converts it to a standardized error response:

```json
{
  "success": false,
  "message": "Error message",
  "errors": [
    {
      "code": "error_code",
      "message": "Detailed error message",
      "field": "field_name",
      "details": { ... }
    }
  ],
  "meta": {
    "timestamp": "2025-03-28T12:34:56.789Z",
    "request_id": "unique-request-id",
    ...
  }
}
```

## Using Exceptions

### Throwing Exceptions

In your code, throw specific exceptions based on the error type:

```python
# Resource not found
if property_data is None:
    raise NotFoundException(
        message=f"Property with ID {property_id} not found",
        details={"property_id": property_id}
    )

# Validation error
if min_units > max_units:
    raise ValidationError(
        message="Minimum units cannot be greater than maximum units",
        details={"min_units": min_units, "max_units": max_units}
    )

# Storage error
if not result.success:
    raise StorageException(
        message="Failed to update property",
        details={"property_id": property_id, "error": result.error}
    )
```

### Exception Handling

In endpoint handlers, use try/except blocks to catch and handle exceptions:

```python
try:
    # Business logic here
    result = await service.do_something()
    return APIResponse.success_response(data=result)
    
except ValidationError:
    # No need to handle - middleware will convert to API response
    raise
    
except Exception as e:
    # Log unexpected errors and convert to appropriate exception
    logger.exception(f"Unexpected error: {str(e)}")
    raise ServerError(message="An unexpected error occurred")
```

## Security Considerations

Error responses should:

1. **Never** include sensitive information (passwords, tokens, etc.)
2. **Never** expose internal implementation details in production
3. Use generic error messages in production
4. Include enough detail for debugging in development
5. Always include a correlation ID for tracing

## Logging

All exceptions are logged with:

1. Exception type and message
2. Request path and method
3. Correlation ID for tracing
4. Stack trace (for unexpected errors)

Development logs include detailed information, while production logs sanitize sensitive details.