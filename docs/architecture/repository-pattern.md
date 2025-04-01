# Repository Pattern Implementation Guide

This document provides guidance on using the repository pattern implemented in the Acquire project.

## Overview

The repository pattern abstracts data access logic away from business logic, providing a clean separation of concerns. This implementation uses the following key components:

1. **Repository Interfaces** - Define methods for data access
2. **Repository Implementations** - Concrete implementations for specific storage backends
3. **Unit of Work** - Manages transactions across multiple repositories
4. **Repository Factory** - Creates repository instances
5. **Adapters** - Convert between standardized models and various formats

## Repository Interfaces

The repository interfaces are defined in `backend/app/interfaces/repository.py`:

- `Repository` - Base repository interface with common CRUD methods
- `PropertyRepository` - Property-specific repository interface
- `BrokerRepository` - Broker-specific repository interface 
- `GraphRepository` - Graph database repository interface

## Repository Implementations

Concrete implementations of the repository interfaces:

- `SupabasePropertyRepository` - Supabase implementation of PropertyRepository
- `SupabaseBrokerRepository` - Supabase implementation of BrokerRepository

## Using Repositories in Services

Services should use repositories through the factory to maintain abstraction:

```python
from backend.app.db.repository_factory import get_repository_factory

class MyService:
    def __init__(self, repository_factory=None):
        factory = repository_factory or get_repository_factory()
        self.property_repository = factory.create_property_repository()
        self.broker_repository = factory.create_broker_repository()
```

## Unit of Work Pattern

The Unit of Work pattern is implemented in `backend/app/db/unit_of_work.py`. It provides transaction support across multiple repositories:

```python
from backend.app.db.unit_of_work import get_unit_of_work

async def create_related_entities():
    async with get_unit_of_work() as uow:
        # Perform operations with uow.property_repository and uow.broker_repository
        property_result = await uow.property_repository.create(property_entity)
        broker_result = await uow.broker_repository.create(broker_entity)
        
        # If any operation fails, all changes will be rolled back
        # If all operations succeed, changes will be committed
```

## Data Models

The repository pattern works with standardized data models:

- `PropertyBase` - Defined in `backend/app/models/property_model.py`
- `BrokerBase` - Defined in `backend/app/models/broker_model.py`

These models serve as the canonical representation of entities throughout the system.

## Adapters

Adapters convert between standardized models and other formats:

- `PropertyAdapter` - Converts property data between formats
- `BrokerAdapter` - Converts broker data between formats

Use adapters when converting between API schemas and standardized models:

```python
from backend.app.adapters.property_adapter import PropertyAdapter

# Convert from API schema to standardized model
standardized_model = PropertyAdapter.from_schema(api_schema)

# Convert from standardized model to API schema
api_schema = PropertyAdapter.to_schema(standardized_model, ApiSchemaClass)
```

## Repository Factory

The repository factory is responsible for creating repository instances:

- `RepositoryFactory` - Creates repositories based on configured storage type
- `get_repository_factory()` - Gets a singleton instance of the factory

## Testing

Test scripts are available in `backend/scripts/architecture/`:

- `test_repository_pattern.py` - Tests the repository pattern implementation

## Best Practices

1. **Always use repositories through services** - Don't access repositories directly from API endpoints
2. **Use the Unit of Work for related operations** - Ensures data consistency
3. **Use standardized models in business logic** - Convert at the boundaries
4. **Don't mix storage types** - Use the factory to abstract storage details
5. **Add proper error handling** - Check success status and handle errors

## Migration Guidelines

When migrating existing code to use the repository pattern:

1. Create a standardized model for your entity
2. Implement an adapter for the entity
3. Create a repository interface
4. Implement the repository for your storage backend
5. Update the repository factory
6. Refactor the service to use the repository
7. Use the Unit of Work for transactions

## Example Flow

1. API request comes in and is handled by an endpoint
2. Endpoint calls a service method
3. Service gets repository instances from the factory
4. Service converts API schema to standardized model using adapter
5. Service performs business logic and repository operations
6. Repository converts standardized model to storage format
7. Repository performs database operations
8. Service converts results back to API schema
9. Endpoint returns response
