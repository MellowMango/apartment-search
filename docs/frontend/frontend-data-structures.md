# Frontend Data Structures

This document outlines the key data structures that will be used by the frontend application, particularly for the property map view, search functionality, and real-time updates.

## Property Data Model

The property data model describes the structure of property data as it will be consumed by the frontend components.

### Basic Property Object (List View)

This is the minimal property object used in list views and map markers:

```typescript
interface BasicProperty {
  id: string;
  name: string;
  address: string;
  city: string;
  state: string;
  zip: string;
  latitude: number;
  longitude: number;
  price: number;
  units: number;
  year_built: number;
  status: 'available' | 'pending' | 'sold';
  cap_rate: number | null;
  image_url: string | null;
  created_at: string;
  updated_at: string;
}
```

### Detailed Property Object

This expanded property object includes all details needed for the property detail view:

```typescript
interface DetailedProperty extends BasicProperty {
  description: string;
  noi: number | null;
  price_per_unit: number;
  broker: {
    id: string;
    name: string;
    email: string;
    phone: string;
    brokerage: {
      id: string;
      name: string;
      website: string;
    }
  };
  images: string[];
  amenities: string[];
  research: {
    neighborhood_stats?: {
      walk_score?: number;
      transit_score?: number;
      bike_score?: number;
    };
    market_trends?: {
      vacancy_rate?: number;
      rent_growth?: number;
      avg_rent?: number;
    };
    investment_potential?: {
      projected_roi?: number;
      value_add_opportunity?: boolean;
      risk_level?: 'low' | 'medium' | 'high';
    };
  };
}
```

### Property List Response

The structure of the response when fetching a list of properties:

```typescript
interface PropertyListResponse {
  items: BasicProperty[];
  pagination: {
    total: number;
    page: number;
    limit: number;
    pages: number;
  };
}
```

## Search and Filter Parameters

These are the parameters used for searching and filtering properties:

```typescript
interface PropertySearchParams {
  // Pagination
  page?: number;
  limit?: number;
  
  // Text search
  search?: string;
  
  // Status filters
  status?: 'available' | 'pending' | 'sold' | 'all';
  
  // Price range
  min_price?: number;
  max_price?: number;
  
  // Units range
  min_units?: number;
  max_units?: number;
  
  // Location filters
  city?: string;
  state?: string;
  zip?: string;
  
  // Map boundary filter (if map view is active)
  bounds?: {
    north: number;
    south: number;
    east: number;
    west: number;
  };
  
  // Year built range
  year_built_min?: number;
  year_built_max?: number;
  
  // Financial filters
  cap_rate_min?: number;
  cap_rate_max?: number;
  
  // Sorting
  sort_by?: 'price' | 'date' | 'units' | 'cap_rate' | 'year_built';
  sort_dir?: 'asc' | 'desc';
}
```

## User Data Models

### User Profile

The structure of the current user's profile data:

```typescript
interface UserProfile {
  id: string;
  email: string;
  name: string;
  created_at: string;
  subscription?: {
    plan: 'free' | 'basic' | 'premium';
    status: 'active' | 'canceled' | 'expired';
    expires_at: string;
  };
  saved_properties: {
    id: string;
    name: string;
    address: string;
    saved_at: string;
  }[];
}
```

### Authentication State

The global authentication state structure:

```typescript
interface AuthState {
  isAuthenticated: boolean;
  user: UserProfile | null;
  token: string | null;
  loading: boolean;
  error: string | null;
}
```

## Real-Time Update Events

### Property Updated Event

The structure of a property update event:

```typescript
interface PropertyUpdatedEvent {
  event: 'property-updated';
  data: {
    property_id: string;
    changes: {
      [key: string]: {
        old: any;
        new: any;
      }
    };
    updated_at: string;
  }
}
```

### New Property Event

The structure of a new property event:

```typescript
interface PropertyCreatedEvent {
  event: 'property-created';
  data: {
    property_id: string;
    name: string;
    city: string;
    state: string;
    price: number;
    units: number;
    created_at: string;
  }
}
```

## Map Component Data

### Map State

The structure of the map component's state:

```typescript
interface MapState {
  center: [number, number]; // [latitude, longitude]
  zoom: number;
  bounds: {
    north: number;
    south: number;
    east: number;
    west: number;
  };
  markers: {
    [id: string]: {
      position: [number, number];
      property: BasicProperty;
    }
  };
  selectedMarker: string | null;
  loading: boolean;
  error: string | null;
}
```

### Cluster Data

The structure for clustered property markers:

```typescript
interface PropertyCluster {
  id: string;
  position: [number, number];
  count: number;
  properties: BasicProperty[];
  bounds: {
    north: number;
    south: number;
    east: number;
    west: number;
  };
}
```

## Application State

### Global State

The structure of the global application state:

```typescript
interface GlobalState {
  auth: AuthState;
  properties: {
    list: BasicProperty[];
    selected: DetailedProperty | null;
    pagination: {
      total: number;
      page: number;
      limit: number;
      pages: number;
    };
    loading: boolean;
    error: string | null;
  };
  map: MapState;
  filters: PropertySearchParams;
  ui: {
    sidebarOpen: boolean;
    activeTab: 'map' | 'list' | 'saved';
    notifications: {
      id: string;
      type: 'info' | 'success' | 'warning' | 'error';
      message: string;
      timestamp: string;
    }[];
  };
}
```

## Component Props

### Property Card Props

Props for the property card component:

```typescript
interface PropertyCardProps {
  property: BasicProperty;
  onClick?: (property: BasicProperty) => void;
  onSave?: (property: BasicProperty) => void;
  isSaved?: boolean;
  compact?: boolean;
}
```

### Property Map Props

Props for the property map component:

```typescript
interface PropertyMapProps {
  properties: BasicProperty[];
  initialCenter?: [number, number];
  initialZoom?: number;
  onBoundsChange?: (bounds: MapState['bounds']) => void;
  onMarkerClick?: (property: BasicProperty) => void;
  selectedPropertyId?: string;
  loading?: boolean;
  error?: string;
}
```

### Search Filters Props

Props for the search filters component:

```typescript
interface SearchFiltersProps {
  filters: PropertySearchParams;
  onChange: (filters: PropertySearchParams) => void;
  onReset: () => void;
  onSaveFilter?: (name: string, filters: PropertySearchParams) => void;
  savedFilters?: {
    id: string;
    name: string;
    filters: PropertySearchParams;
  }[];
  loading?: boolean;
}
```

## Usage Examples

### Fetching Properties

Example of fetching properties with the defined structures:

```typescript
// Using React Query
const fetchProperties = async (params: PropertySearchParams): Promise<PropertyListResponse> => {
  const queryString = new URLSearchParams();
  
  // Add all non-undefined params to query string
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined) {
      if (key === 'bounds' && typeof value === 'object') {
        // Handle bounds object
        Object.entries(value).forEach(([boundKey, boundValue]) => {
          queryString.append(`bounds[${boundKey}]`, boundValue.toString());
        });
      } else {
        queryString.append(key, value.toString());
      }
    }
  });
  
  const response = await fetch(`/api/v1/properties?${queryString.toString()}`);
  
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.message || 'Failed to fetch properties');
  }
  
  return response.json();
};

// In a React component
const PropertiesList = () => {
  const [filters, setFilters] = useState<PropertySearchParams>({
    page: 1,
    limit: 20,
    status: 'available'
  });
  
  const { data, isLoading, error } = useQuery(
    ['properties', filters],
    () => fetchProperties(filters),
    { keepPreviousData: true }
  );
  
  // Component implementation
};
```

### Updating the Map on Bounds Change

Example of updating properties when the map bounds change:

```typescript
const PropertyMap = ({ onBoundsChange }: PropertyMapProps) => {
  const map = useMapEvents({
    moveend: () => {
      const bounds = map.getBounds();
      const newBounds = {
        north: bounds.getNorth(),
        south: bounds.getSouth(),
        east: bounds.getEast(),
        west: bounds.getWest()
      };
      
      onBoundsChange?.(newBounds);
    }
  });
  
  // Map implementation
};

// In parent component
const MapView = () => {
  const [filters, setFilters] = useState<PropertySearchParams>({
    status: 'available',
    limit: 100
  });
  
  const handleBoundsChange = (bounds: MapState['bounds']) => {
    setFilters(prev => ({
      ...prev,
      bounds
    }));
  };
  
  return (
    <PropertyMap
      properties={properties}
      onBoundsChange={handleBoundsChange}
    />
  );
};
```

### Handling Real-Time Updates

Example of handling real-time property updates:

```typescript
const useRealTimeUpdates = () => {
  const dispatch = useDispatch();
  const socket = useRef<Socket | null>(null);
  
  useEffect(() => {
    // Connect to Socket.IO server
    socket.current = io('/');
    
    // Listen for property updates
    socket.current.on('property-updated', (event: PropertyUpdatedEvent) => {
      dispatch({
        type: 'PROPERTY_UPDATED',
        payload: event.data
      });
      
      // Show notification
      dispatch({
        type: 'ADD_NOTIFICATION',
        payload: {
          id: uuidv4(),
          type: 'info',
          message: `Property "${event.data.property_id}" has been updated`,
          timestamp: new Date().toISOString()
        }
      });
    });
    
    // Listen for new properties
    socket.current.on('property-created', (event: PropertyCreatedEvent) => {
      dispatch({
        type: 'PROPERTY_CREATED',
        payload: event.data
      });
      
      // Show notification
      dispatch({
        type: 'ADD_NOTIFICATION',
        payload: {
          id: uuidv4(),
          type: 'success',
          message: `New property added: ${event.data.name}`,
          timestamp: new Date().toISOString()
        }
      });
    });
    
    return () => {
      socket.current?.disconnect();
    };
  }, [dispatch]);
};
```

These data structures and usage examples provide a foundation for building the frontend application, ensuring consistent data handling and component interactions.