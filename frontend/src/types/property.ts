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
  // Core property fields
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
  square_feet?: number;
  cap_rate?: number;
  property_type?: string;
  property_status?: string;
  status?: string;
  description?: string;
  amenities?: Record<string, any>;
  images?: string[];
  image_url?: string;
  broker_id?: string;
  broker?: string;
  is_multifamily?: boolean;
  created_at?: string;
  updated_at?: string;
  _highlight?: boolean;

  // Location and geocoding fields
  latitude?: number;
  longitude?: number;
  verified_address?: string;
  geocoded_at?: string;
  
  // Data quality and validation flags
  _coordinates_missing?: boolean;
  _needs_geocoding?: boolean;
  _geocoded?: boolean;
  _is_grid_pattern?: boolean;
  _is_invalid_range?: boolean;
  _outside_austin?: boolean;
  _coordinates_from_research?: boolean;
  _is_test_property?: boolean;
  non_multifamily_detected?: boolean;
  
  // Geocoding process fields
  _geocoding_source?: 'existing' | 'verified_address' | 'full_address' | 'property_name';
  _geocoding_failed?: boolean;
  
  // Data normalization and cleaning
  _data_cleaned?: boolean;
  _cleaning_notes?: string;
  _data_quality_issues?: string[];
  cleaning_note?: string;
  
  // Enrichment fields
  _data_enriched?: boolean;
  _enrichment_notes?: string;
  _investment_metrics?: {
    noi?: number;
    cap_rate?: number;
    price_per_sqft?: number;
    occupancy_rate?: number;
  };
  _market_analysis?: {
    market_rent?: number;
    comp_properties?: string[];
    market_vacancy?: number;
  };
  _risk_assessment?: {
    risk_score?: number;
    risk_factors?: string[];
  };
  
  // Research and additional data
  _research?: any;
  _additional_data?: Record<string, any>;
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