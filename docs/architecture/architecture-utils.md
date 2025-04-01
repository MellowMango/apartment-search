# Architecture Utilities Guide

This guide explains how to use the architecture utilities introduced as part of our system architecture improvement.

## Overview

The architecture utilities provide tools to:

1. Tag components with their architectural layer
2. Track and validate layer dependencies
3. Log cross-layer calls for monitoring
4. Document system architecture

## Getting Started

### 1. Tagging Components with Layers

Use the `@layer` decorator to tag your classes with their architectural layer:

```python
from backend.app.utils.architecture import layer, ArchitectureLayer

@layer(ArchitectureLayer.PROCESSING)
class MyDataProcessor:
    """This class processes data in some way."""
    
    def process(self, data):
        # Implementation
        pass
```

Available layers:
- `ArchitectureLayer.SOURCE` - External data sources
- `ArchitectureLayer.COLLECTION` - Components that collect data
- `ArchitectureLayer.PROCESSING` - Components that process and transform data
- `ArchitectureLayer.STORAGE` - Components that store and retrieve data
- `ArchitectureLayer.API` - API endpoints and related components
- `ArchitectureLayer.SCHEDULED` - Scheduled tasks and jobs
- `ArchitectureLayer.CONSUMER` - Client applications and services

### 2. Implementing Interfaces

Each layer has interface definitions in the `backend.app.interfaces` package:

```python
from backend.app.interfaces.processing import DataProcessor
from backend.app.utils.architecture import layer, ArchitectureLayer

@layer(ArchitectureLayer.PROCESSING)
class MyCustomProcessor(DataProcessor):
    """Custom implementation of the DataProcessor interface."""
    
    async def process_item(self, item):
        # Implementation
        pass
        
    async def process_batch(self, items):
        # Implementation
        pass
```

### 3. Logging Cross-Layer Calls

Use the `log_cross_layer_call` decorator to log and monitor calls between layers:

```python
from backend.app.utils.architecture import log_cross_layer_call, ArchitectureLayer

@log_cross_layer_call(ArchitectureLayer.PROCESSING, ArchitectureLayer.STORAGE)
async def save_processed_data(data):
    """Save processed data to storage."""
    # Implementation
    pass
```

### 4. Checking Layer Membership

You can check which layer a component belongs to:

```python
from backend.app.utils.architecture import get_layer

# Check layer of a class
layer = get_layer(MyDataProcessor)
if layer == ArchitectureLayer.PROCESSING:
    print("This is a processing component")
```

## Best Practices

1. **Tag all new components** with their appropriate layer
2. **Implement the interfaces** defined for each layer
3. **Keep dependencies flowing downward** through the layers
4. **Avoid circular dependencies** between layers
5. **Log cross-layer calls** for monitoring and debugging

## Example: Converting Existing Components

When converting existing components to use the new architecture:

1. Add the appropriate `@layer` decorator
2. Implement the corresponding interface
3. Update dependencies to follow the layered pattern
4. Add logging for cross-layer calls

### Before:

```python
class PropertyService:
    def __init__(self, db_client):
        self.db = db_client
        
    def get_properties(self, filters):
        # Implementation
        pass
```

### After:

```python
from backend.app.interfaces.api import DataProvider
from backend.app.utils.architecture import layer, ArchitectureLayer, log_cross_layer_call

@layer(ArchitectureLayer.API)
class PropertyService(DataProvider):
    def __init__(self, db_client):
        self.db = db_client
        
    @log_cross_layer_call(ArchitectureLayer.API, ArchitectureLayer.STORAGE)
    async def get_by_id(self, entity_id):
        return await self.db.get_property(entity_id)
        
    @log_cross_layer_call(ArchitectureLayer.API, ArchitectureLayer.STORAGE)
    async def query(self, filters, pagination):
        return await self.db.query_properties(filters, pagination)
```

## Tools for Architecture Analysis

The architecture utilities include tools to analyze your codebase:

```python
from backend.app.utils.architecture import get_all_tagged_classes

# Get all classes tagged with layers
tagged_classes = get_all_tagged_classes()
for layer, classes in tagged_classes.items():
    print(f"Layer: {layer.value}")
    for cls in classes:
        print(f"  - {cls}")
```

## Migration Phase Tracking

As you tag components, track your progress in the migration plan document:

```
/docs/architecture-migration-plan.md
```

Update the status of components as they're migrated to the new architecture.