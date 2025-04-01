# Data Access Patterns Guide

This document describes the data access patterns used in the Acquire project.

## Overview

The Acquire project uses a layered architecture with a clear separation of concerns for data access. The main patterns used are:

1. **Repository Pattern** - Abstracts data access logic
2. **Unit of Work Pattern** - Coordinates transactions
3. **Adapter Pattern** - Converts between data formats
4. **Factory Pattern** - Creates repository instances

These patterns work together to provide a clean, maintainable, and testable approach to data access.

## Repository Pattern

The Repository pattern provides a standardized interface for data access operations, abstracting the underlying database implementation. This allows services to work with repositories without knowing the details of how data is stored.

See the [Repository Pattern Guide](./repository-pattern.md) for detailed implementation information.

## Unit of Work Pattern

The Unit of Work pattern coordinates transactions across multiple repositories, ensuring that data remains consistent when operations span multiple entities.

See the [Unit of Work Pattern Guide](./unit-of-work-pattern.md) for detailed implementation information.

## Adapter Pattern

The Adapter pattern converts between different data representations, particularly between:

1. **Standardized Models** - Used throughout the system
2. **API Schemas** - Used for API requests and responses
3. **Legacy Data Formats** - Used for backward compatibility

Adapters help maintain clean boundaries between architectural layers.

### Key Adapters:

- `PropertyAdapter` - Converts property data between formats
- `BrokerAdapter` - Converts broker data between formats

## Factory Pattern

The Factory pattern is used to create repository instances, allowing for:

1. **Abstraction** - Services don't need to know which repository implementation to use
2. **Configuration** - Repository type can be configured based on environment
3. **Testing** - Easy repository mocking for tests

### Implementation:

The `RepositoryFactory` interface is defined in `backend/app/interfaces/repository.py` and implemented in `backend/app/db/repository_factory.py`.

```python
# Get the factory
factory = get_repository_factory()

# Create repositories
property_repository = factory.create_property_repository()
broker_repository = factory.create_broker_repository()
```

## Storage Layer Organization

The Storage layer is organized as follows:

```
backend/app/
├── interfaces/          # Interface definitions
│   ├── repository.py    # Repository interfaces
│   └── storage.py       # Storage result/query classes
├── db/                  # Database implementations
│   ├── repository_factory.py      # Factory implementation
│   ├── unit_of_work.py           # Unit of Work implementation
│   ├── supabase_client.py        # Supabase client
│   ├── supabase_repository.py    # Property repository
│   ├── supabase_broker_repository.py  # Broker repository
│   └── neo4j_client.py          # Neo4j client
├── models/              # Standardized data models
│   ├── property_model.py # Property model
│   └── broker_model.py   # Broker model
└── adapters/            # Data conversion adapters
    ├── property_adapter.py # Property adapter
    └── broker_adapter.py   # Broker adapter
```

## Data Flow

The typical data flow through the system is:

1. **API Layer** - Receives request with API schema
2. **Service Layer** - Uses adapter to convert to standardized model
3. **Service Layer** - Performs business logic using standardized model
4. **Repository Layer** - Uses adapter to convert to storage format
5. **Repository Layer** - Performs database operations
6. **Repository Layer** - Converts result back to standardized model
7. **Service Layer** - Uses adapter to convert to API schema
8. **API Layer** - Returns response with API schema

## Data Validation

Data validation happens at multiple levels:

1. **API Schema Level** - Using Pydantic validators in API schemas
2. **Standardized Model Level** - Using Pydantic validators in models
3. **Repository Level** - Pre-database validation
4. **Database Level** - Using database constraints

## Best Practices

1. **Keep layers clean** - Don't bypass layers
2. **Use adapters at boundaries** - Convert between formats at layer boundaries
3. **Validate early** - Catch errors before they reach the database
4. **Use Unit of Work for transactions** - Maintain data consistency
5. **Return meaningful errors** - Help callers understand what went wrong

## Future Enhancements

Planned enhancements to the data access patterns:

1. **Caching Layer** - Add caching to repositories for performance
2. **Event System** - Add events for entity changes
3. **Audit Logging** - Log all data modifications
4. **Multi-database Support** - Support more database types
5. **Real-time Updates** - Push data changes to clients

## Testing

To test the data access patterns:

```bash
# Run the repository pattern tests
python -m backend.scripts.architecture.test_repository_pattern

# Run specific tests
pytest backend/tests/test_repositories.py
```

## Related Documentation

- [Repository Pattern Guide](./repository-pattern.md)
- [Unit of Work Pattern Guide](./unit-of-work-pattern.md)
- [Architecture Migration Plan](./architecture-migration-plan.md)
