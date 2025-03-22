export interface Broker {
  id: string;
  name: string;
  email?: string;
  phone?: string;
  brokerage?: {
    id: string;
    name: string;
    website?: string;
  };
}

export interface Property {
  id: string;
  name: string;
  address: string;
  city: string;
  state: string;
  zip_code?: string;
  latitude: number;
  longitude: number;
  price?: number;
  num_units?: number; // Some properties use num_units
  units?: number;     // Some might use units
  year_built?: number;
  year_renovated?: number;
  status: string;
  description?: string;
  cap_rate?: number;
  noi?: number;
  occupancy?: number;
  avg_rent?: number;
  lot_size?: number;
  building_size?: number;
  property_type?: string;
  image_url?: string;
  images?: string[];
  broker?: Broker;
  broker_id?: string;
  brokerage_id?: string;
  created_at?: string;
  updated_at?: string;
  geocoded_at?: string;
  verified_address?: string;  // Field for Google Maps verified address
  amenities?: string[];
  
  // Flags for coordinate status
  _coordinates_missing?: boolean;  // Flag for properties without valid coordinates
  _needs_geocoding?: boolean;      // Flag for properties that need geocoding
  _geocoded?: boolean;             // Flag for properties that were geocoded
  _is_grid_pattern?: boolean;      // Flag for properties with coordinates in a grid pattern
  _is_invalid_range?: boolean;     // Flag for properties with coordinates outside valid ranges
  _outside_austin?: boolean;       // Flag for properties with coordinates outside Austin area
  _coordinates_from_research?: boolean; // Flag for coordinates that came from research
  _is_test_property?: boolean;     // Flag for test properties
  _highlight?: boolean;            // Flag for highlighting properties in the UI
}

export interface PropertySearchParams {
  page?: number;
  limit?: number;
  search?: string;
  status?: string;
  min_price?: number;
  max_price?: number;
  min_units?: number;
  max_units?: number;
  city?: string;
  state?: string;
  zip?: string;
  bounds?: {
    north: number;
    south: number;
    east: number;
    west: number;
  };
  year_built_min?: number;
  year_built_max?: number;
  cap_rate_min?: number;
  cap_rate_max?: number;
  sort_by?: string;
  sort_dir?: 'asc' | 'desc';
}

export interface PropertyListResponse {
  items: Property[];
  pagination: {
    total: number;
    page: number;
    limit: number;
    pages: number;
  };
}