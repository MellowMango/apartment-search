# Unit of Work Pattern Implementation Guide

This document describes the Unit of Work pattern implemented in the Acquire project for managing transactions across multiple repositories.

## Overview

The Unit of Work pattern helps maintain data consistency by ensuring that multiple operations are treated as a single transaction. If any operation fails, all changes will be rolled back.

## Implementation

The Unit of Work implementation in `backend/app/db/unit_of_work.py` provides:

1. **Transaction boundaries** - Defines the begin and end of transactions
2. **Repository access** - Provides access to repositories within a transaction
3. **Commit and rollback** - Manages transaction completion
4. **Error handling** - Automatically rolls back on exceptions

## Using the Unit of Work

The recommended way to use the Unit of Work is through the `get_unit_of_work` context manager:

```python
from backend.app.db.unit_of_work import get_unit_of_work

async def update_property_and_broker(property_id, broker_id, property_data, broker_data):
    async with get_unit_of_work() as uow:
        # Get entities
        property_entity = await uow.property_repository.get(property_id)
        broker_entity = await uow.broker_repository.get(broker_id)
        
        if not property_entity or not broker_entity:
            raise ValueError("Property or broker not found")
        
        # Update entities
        for key, value in property_data.items():
            setattr(property_entity, key, value)
        
        for key, value in broker_data.items():
            setattr(broker_entity, key, value)
        
        # Save changes
        property_result = await uow.property_repository.update(property_id, property_entity)
        broker_result = await uow.broker_repository.update(broker_id, broker_entity)
        
        # Link entities
        # ... other operations
        
        # Changes will be committed when exiting the context manager
        # If any exception occurs, all changes will be rolled back
```

## Features

### Transaction Management

The Unit of Work manages the transaction lifecycle:

1. Start transaction when entering the context
2. Commit changes on successful completion
3. Rollback changes if an exception occurs

### Repository Access

The Unit of Work provides access to repositories:

```python
async with get_unit_of_work() as uow:
    # Access properties repository
    properties = await uow.property_repository.list(filters)
    
    # Access brokers repository
    brokers = await uow.broker_repository.list(filters)
```

### Error Handling

Exceptions within the Unit of Work context will cause automatic rollback:

```python
try:
    async with get_unit_of_work() as uow:
        # Perform operations
        # ...
        # If any operation raises an exception, changes will be rolled back
except Exception as e:
    # Handle the exception
    logger.error(f"Transaction failed: {str(e)}")
```

## Current Limitations

The current implementation has some limitations:

1. **Supabase transaction support** - The JavaScript Supabase client doesn't directly support transactions. The Unit of Work provides logical transaction boundaries, but actual database transactions are not implemented yet.

2. **Cross-database transactions** - Transactions spanning multiple database types (e.g., Supabase and Neo4j) are not fully supported.

## Best Practices

1. **Use Unit of Work for related operations** - Use the Unit of Work pattern whenever operations need to be atomic.

2. **Keep transactions short** - Avoid long-running operations within a transaction.

3. **Don't access repositories directly** - Always use repositories through the Unit of Work for operations that require transactional integrity.

4. **Handle exceptions** - Properly handle exceptions outside the Unit of Work context.

5. **Validate before transaction** - Perform validation before entering the transaction to avoid unnecessary rollbacks.

## Future Improvements

Planned improvements to the Unit of Work implementation:

1. **Real database transactions** - Implement actual database transactions for Supabase when available.

2. **Cross-database transactions** - Improve support for transactions spanning multiple database types.

3. **Nested transactions** - Support for nested transactions.

4. **Transaction isolation levels** - Support for different transaction isolation levels.

## Example Scenarios

### Creating Related Entities

```python
async def create_property_with_broker(property_data, broker_data):
    async with get_unit_of_work() as uow:
        # Create broker
        broker_entity = BrokerBase(**broker_data)
        broker_result = await uow.broker_repository.create(broker_entity)
        
        if not broker_result.success:
            raise ValueError(f"Failed to create broker: {broker_result.error}")
        
        # Add broker ID to property data
        property_data["broker_id"] = broker_result.entity_id
        
        # Create property
        property_entity = PropertyBase(**property_data)
        property_result = await uow.property_repository.create(property_entity)
        
        if not property_result.success:
            raise ValueError(f"Failed to create property: {property_result.error}")
        
        return {
            "property_id": property_result.entity_id,
            "broker_id": broker_result.entity_id
        }
```

### Updating Multiple Entities

```python
async def batch_update_properties(updates):
    async with get_unit_of_work() as uow:
        results = []
        
        for property_id, property_data in updates.items():
            property_entity = await uow.property_repository.get(property_id)
            
            if not property_entity:
                results.append({
                    "property_id": property_id,
                    "success": False,
                    "error": "Property not found"
                })
                continue
            
            # Update entity
            for key, value in property_data.items():
                setattr(property_entity, key, value)
            
            # Save changes
            result = await uow.property_repository.update(property_id, property_entity)
            
            results.append({
                "property_id": property_id,
                "success": result.success,
                "error": result.error
            })
        
        return results
```
