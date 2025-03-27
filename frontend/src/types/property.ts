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
  id: string | number;
  name?: string;
  address?: string;
  city?: string;
  state?: string;
  zip?: string;
  units?: number;
  num_units?: number;
  price?: number;
  price_per_unit?: number;
  year_built?: number;
  latitude?: number;
  longitude?: number;
  status?: string;
  property_status?: string;
  created_at?: string;
  updated_at?: string;
  broker?: string;
  image_url?: string;
  description?: string;
  _highlight?: boolean;
  
  // Geocoding-related fields
  verified_address?: string;
  geocoded_at?: string;
  
  // Coordinate status flags
  _coordinates_missing?: boolean;
  _needs_geocoding?: boolean;
  _geocoded?: boolean;
  _is_grid_pattern?: boolean;
  _is_invalid_range?: boolean;
  _outside_austin?: boolean;
  _coordinates_from_research?: boolean;
  _is_test_property?: boolean;
  
  // Enhanced geocoding fields
  _geocoding_source?: 'existing' | 'verified_address' | 'full_address' | 'property_name';
  _geocoding_failed?: boolean;
  
  // Data cleaning fields
  _data_cleaned?: boolean;
  _cleaning_notes?: string;
  _data_quality_issues?: string[];
  
  // Data enrichment fields
  _data_enriched?: boolean;
  _enrichment_notes?: string;
  
  // Research data
  _research?: any;
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