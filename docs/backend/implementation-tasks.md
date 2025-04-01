# Architecture Migration Implementation Tasks

## Phase 1: Initial Setup and Layer Definition

### Week 1: Interface Definition

| Task ID | Description | Assignee | Status | Due Date | Notes |
|---------|-------------|----------|--------|----------|-------|
| P1-1 | Create interfaces directory structure | | Completed | 2025-03-27 | Created `backend/app/interfaces/` |
| P1-2 | Define collection interfaces | | Completed | 2025-03-27 | Defined `DataSourceCollector` in `collection.py` |
| P1-3 | Define processing interfaces | | Completed | 2025-03-27 | Defined `DataProcessor`, `DataFilter` in `processing.py` |
| P1-4 | Define storage interfaces | | Completed | 2025-03-27 | Defined `StorageReader`, `StorageWriter` in `storage.py` |
| P1-5 | Define API interfaces | | Completed | 2025-03-27 | Defined `DataProvider` in `api.py` |
| P1-5.1 | Define Scheduled interfaces | | Completed | 2025-03-27 | Defined `ScheduledTask` in `scheduled.py` |
| P1-6 | Create layer documentation utilities | | Completed | 2025-03-27 | Created `@layer` decorator in `architecture.py` |
| P1-7 | Set up test harness for interfaces | | Completed | 2025-03-27 | Using demo script to verify interfaces |

### Week 2: Documentation and Monitoring

| Task ID | Description | Assignee | Status | Due Date | Notes |
|---------|-------------|----------|--------|----------|-------|
| P1-8 | Tag data collection components | | Completed | 2025-03-27 | Tagged all data collection components including scrapers and collectors |
| P1-9 | Tag data processing components | | Completed | 2025-03-27 | Tagged all enrichers including `PropertyProfiler`, `MarketAnalyzer`, `RiskAssessor` |
| P1-10 | Tag storage components | | Completed | 2025-03-27 | Tagged all storage components with proper architectural layer |
| P1-11 | Tag API components | | Completed | 2025-03-27 | Tagged all API endpoints and services including `BrokerService` |
| P1-11.1 | Tag scheduled components | | Completed | 2025-03-27 | Tagged all scheduled components with proper architectural layer |
| P1-12 | Set up performance logging middleware | | Completed | 2025-03-27 | Added cross-layer logging decorator |
| P1-13 | Create metrics collector | | Completed | 2025-03-27 | Added metrics collection in monitoring.py |
| P1-14 | Set up basic monitoring dashboard | | Completed | 2025-03-27 | Using logging dashboard for now |

### Week 3: Data Models

| Task ID | Description | Assignee | Status | Due Date | Notes |
|---------|-------------|----------|--------|----------|-------|
| P1-15 | Define core property data model | | Completed | 2025-03-27 | Created `PropertyBase` in `property_model.py` |
| P1-16 | Create broker data model | | Completed | 2025-03-27 | Added broker info to property model |
| P1-17 | Create geocoding data model | | Completed | 2025-03-27 | Created `Coordinates` model in `property_model.py` |
| P1-18 | Write adapter functions for legacy compatibility | | Completed | 2025-03-27 | Created `PropertyAdapter` in `property_adapter.py` |
| P1-19 | Implement validation test cases | | In Progress | 2025-03-27 | Started adding validation in models |
| P1-20 | Document data model migration path | | Completed | 2025-03-27 | Added to migration progress doc |
| P1-21 | Phase 1 review meeting | | Not Started | 2025-03-28 | Scheduled for tomorrow |

### Week 4: Interface Implementations

| Task ID | Description | Assignee | Status | Due Date | Notes |
|---------|-------------|----------|--------|----------|-------|
| P1-22 | Implement DataFilter interface | | Completed | 2025-03-27 | Implemented on NonMultifamilyDetector |
| P1-23 | Implement DataProcessor interface | | Completed | 2025-03-27 | Implemented on PropertyResearcher |
| P1-24 | Implement Storage interfaces | | Completed | 2025-03-27 | Implemented StorageReader/Writer on SupabaseStorage |
| P1-25 | Implement DataProvider interface | | Completed | 2025-03-27 | Implemented on PropertyService |
| P1-26 | Implement ScheduledTask interface | | Completed | 2025-03-27 | Implemented on BatchGeocodingTask |
| P1-27 | Create architecture demo script | | Completed | 2025-03-27 | Created `demo_architecture.py` |
| P1-28 | Update Phase 1 documentation | | Completed | 2025-03-27 | Updated migration progress and plans |

## Critical Path Dependencies

```
P1-1 → P1-2, P1-3, P1-4, P1-5, P1-5.1 → P1-7 → P1-22, P1-23, P1-24, P1-25, P1-26
P1-6 → P1-8, P1-9, P1-10, P1-11, P1-11.1
P1-12 → P1-13 → P1-14
P1-15, P1-16, P1-17 → P1-18 → P1-19, P1-20
P1-22, P1-23, P1-24, P1-25, P1-26 → P1-27 → P1-28
All tasks → P1-21
```

## Next Steps

1. Complete the tagging of remaining components (P1-8, P1-9, P1-10, P1-11, P1-11.1)
2. Complete the implementation of DataProvider interface on PropertyService (P1-25)
3. Complete DataSourceCollector implementations for other scraper classes (P1-30, P1-31)
4. Finish test coverage for collector interfaces (P1-34)
5. Implement property tracking for collection results (P1-33)
6. Prepare for Phase 2 focused on Data Processing Layer reorganization

These tasks will help us complete Phase 1 and prepare for Phase 2 of the architecture migration. As we've completed key implementations on all layers, we're ready to start using the new flow for ACR Multifamily and CBRE scrapers while continuing to implement the remaining collectors.

## New Implementation Tasks

### Week 5: Additional Interface Implementations

| Task ID | Description | Assignee | Status | Due Date | Notes |
|---------|-------------|----------|--------|----------|-------|
| P1-29 | Implement DataSourceCollector for ACR Multifamily | | Completed | 2025-03-27 | Created ACRMultifamilyCollector |
| P1-30 | Implement DataSourceCollector for CRE Deal Flow | | Completed | 2025-03-27 | Created CBREDealFlowCollector |
| P1-31 | Implement DataSourceCollector for other scrapers | | Completed | 2025-03-27 | Implemented MultifamilyGroupCollector, MarcusMillichapCollector, WalkerDunlopCollector |
| P1-32 | Update demo script to show full data flow | | Completed | 2025-03-27 | Updated demo_architecture.py to show complete flow |
| P1-33 | Implement property tracking for collection results | | Completed | 2025-03-27 | Track property origin from collector, added to CollectionResult and PropertyStorage |
| P1-34 | Create automated tests for the collector interfaces | | In Progress | 2025-03-27 | Created test scripts for ACR and CBRE Deal Flow |
| P1-35 | Create unified collector demo script | | Completed | 2025-03-27 | Created run_all_collectors.py |
| P1-36 | Test PropertyService DataProvider implementation | | Completed | 2025-03-27 | Created test_property_service.py |

## Code Samples for Initial Tasks

### Task P1-1: Interface Directory Structure

Create the following directory and files:

```
backend/app/interfaces/
├── __init__.py
├── collection.py
├── processing.py
├── storage.py
└── api.py
```

### Task P1-6: Layer Documentation Utilities

```python
# backend/app/utils/architecture.py

from enum import Enum
from typing import Type, TypeVar, Dict, Any, Optional
import functools

class ArchitectureLayer(str, Enum):
    """Enumeration of architecture layers"""
    SOURCE = "source"
    COLLECTION = "collection"
    PROCESSING = "processing" 
    STORAGE = "storage"
    API = "api"
    SCHEDULED = "scheduled"
    CONSUMER = "consumer"

T = TypeVar('T')

def layer(layer_name: ArchitectureLayer) -> callable:
    """Decorator to mark a class as belonging to a specific architecture layer
    
    Example:
        @layer(ArchitectureLayer.PROCESSING)
        class MyProcessor:
            pass
    """
    def decorator(cls: Type[T]) -> Type[T]:
        setattr(cls, '_architecture_layer', layer_name)
        return cls
    return decorator

def get_layer(cls: Type[Any]) -> Optional[ArchitectureLayer]:
    """Get the architecture layer of a class"""
    return getattr(cls, '_architecture_layer', None)

def log_between_layers(source_layer: ArchitectureLayer, target_layer: ArchitectureLayer):
    """Decorator to log calls between architecture layers
    
    Example:
        @log_between_layers(ArchitectureLayer.PROCESSING, ArchitectureLayer.STORAGE)
        def save_to_database(data):
            pass
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Add logging here
            print(f"Call from {source_layer} to {target_layer}: {func.__name__}")
            return func(*args, **kwargs)
        return wrapper
    return decorator
```

### Task P1-15: Core Property Data Model

```python
# backend/app/models/property.py

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, validator
import uuid

class Address(BaseModel):
    """Address representation for properties"""
    street: str
    city: str
    state: str
    zip_code: str
    
    class Config:
        extra = "allow"  # For backward compatibility

class Coordinates(BaseModel):
    """Geographic coordinates"""
    latitude: float
    longitude: float
    accuracy: Optional[float] = None
    
    class Config:
        extra = "allow"

class PropertyBase(BaseModel):
    """Base model for property data throughout the system"""
    property_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: Optional[str] = None
    address: Address
    coordinates: Optional[Coordinates] = None
    units: Optional[int] = None
    is_multifamily: bool = True
    non_multifamily_detected: bool = False
    cleaning_note: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        extra = "allow"  # Allow extra fields for backward compatibility
    
    @validator('updated_at', always=True)
    def set_updated_at(cls, v, values, **kwargs):
        """Always set updated_at to the current time"""
        return datetime.utcnow()

# Legacy adapter functions to be implemented
def from_legacy_dict(legacy_data: Dict[str, Any]) -> PropertyBase:
    """Convert legacy property format to standardized model"""
    # Implementation to be added
    pass

def to_legacy_dict(property_data: PropertyBase) -> Dict[str, Any]:
    """Convert standardized model to legacy format"""
    # Implementation to be added
    pass
```