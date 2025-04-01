import { Property } from '../types/property';

// Initialize with your backend API URL - choose the right URL based on environment
const API_URL = typeof window !== 'undefined' 
  ? (
      // For local development, use relative URL
      window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
        ? '/api'
        // For production, use the configured API URL
        : (process.env.NEXT_PUBLIC_API_URL || '/api')
    )
  : '/api';

/**
 * Get user JWT token for authenticated requests
 */
const getUserToken = (): string | null => {
  // If in a browser environment
  if (typeof window !== 'undefined') {
    try {
      // Try to get the token from Supabase Auth
      // First check if we have access to the Supabase client
      if (typeof window.localStorage !== 'undefined') {
        // Look for token in local storage
        // Check new Supabase v2 format first
        const supabaseSession = localStorage.getItem('sb-' + process.env.NEXT_PUBLIC_SUPABASE_URL?.replace(/^https?:\/\//, '') + '-auth-token');
        if (supabaseSession) {
          try {
            const session = JSON.parse(supabaseSession);
            if (session?.access_token) {
              return session.access_token;
            }
          } catch (e) {
            console.error('Error parsing Supabase session:', e);
          }
        }
        
        // Fallback to old format
        const supabaseAuth = localStorage.getItem('supabase.auth.token');
        if (supabaseAuth) {
          try {
            const parsedAuth = JSON.parse(supabaseAuth);
            return parsedAuth.currentSession?.access_token || null;
          } catch (e) {
            console.error('Error parsing legacy auth token:', e);
          }
        }
      }
    } catch (e) {
      console.error('Error getting auth token:', e);
    }
  }
  return null;
};

/**
 * Standard interface for API error responses
 */
export interface ApiError {
  code: string;
  message: string;
  details?: any;
}

/**
 * Standard interface for API success responses
 */
export interface ApiResponse<T> {
  success: boolean;
  data: T;
  message?: string;
  error?: ApiError;
}

/**
 * Call the backend API with proper headers and error handling
 * 
 * @param endpoint API endpoint path (e.g., '/properties')
 * @param options Fetch options
 * @returns Promise resolving to the data from the API
 * @throws Error if the request fails
 */
export async function fetchFromAPI<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  // Add authorization if a token is available
  const token = getUserToken();
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(options.headers as Record<string, string> || {}),
  };

  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  // Make the request
  const response = await fetch(`${API_URL}${endpoint}`, {
    ...options,
    headers,
    credentials: 'include',
    mode: 'cors'
  });

  // Handle HTTP error responses
  if (!response.ok) {
    // Check for specific status codes
    if (response.status === 401) {
      const error = new Error('Authentication required. Please log in.');
      (error as any).code = 'unauthorized';
      throw error;
    }
    
    if (response.status === 403) {
      const error = new Error('You do not have permission to access this resource.');
      (error as any).code = 'forbidden';
      throw error;
    }
    
    if (response.status === 404) {
      const error = new Error('Resource not found.');
      (error as any).code = 'not_found';
      throw error;
    }
    
    if (response.status === 429) {
      const error = new Error('Too many requests. Please try again later.');
      (error as any).code = 'rate_limit_exceeded';
      throw error;
    }
    
    // For any other error, try to parse the response
    try {
      const errorData = await response.json();
      const error = new Error(errorData.message || 'An error occurred');
      (error as any).code = errorData.code || 'api_error';
      (error as any).status = response.status;
      (error as any).details = errorData.details || null;
      throw error;
    } catch (parseError) {
      // If the response can't be parsed as JSON, throw a generic error
      const error = new Error(`API error: ${response.status} ${response.statusText}`);
      (error as any).code = 'api_error';
      (error as any).status = response.status;
      throw error;
    }
  }

  // Try to parse the response as JSON
  try {
    const data = await response.json() as ApiResponse<T>;

    // Check if the response has a success field and is successful
    if (data && typeof data.success === 'boolean') {
      if (!data.success) {
        const error = new Error(data.error?.message || data.message || 'API request failed');
        (error as any).code = data.error?.code || 'api_error';
        (error as any).details = data.error?.details || null;
        throw error;
      }
      
      // Return just the data portion for successful responses
      return data.data;
    }
    
    // If the response doesn't have a success field, assume it's the data directly
    return data as unknown as T;
  } catch (e) {
    // If the response can't be parsed as JSON, throw an error
    if (e instanceof SyntaxError) {
      const error = new Error('Invalid response format from API');
      (error as any).code = 'invalid_response';
      throw error;
    }
    
    // Re-throw other errors
    throw e;
  }
}

/**
 * Interface for map property fetch options
 */
export interface MapPropertiesOptions {
  bounds?: {
    north: number;
    south: number;
    east: number;
    west: number;
  };
  page?: number;
  pageSize?: number;
  showAvailable?: boolean;
  showUnderContract?: boolean;
  showSold?: boolean;
}

/**
 * Fetch properties for map display with filtering options
 * 
 * @param options Options for filtering properties
 * @returns Promise resolving to array of properties
 */
export async function fetchMapProperties(options: MapPropertiesOptions = {}): Promise<Property[]> {
  // Generate filter parameters from options
  const params = new URLSearchParams();

  // Map bounds parameters
  if (options.bounds) {
    params.append('north', options.bounds.north.toString());
    params.append('south', options.bounds.south.toString());
    params.append('east', options.bounds.east.toString());
    params.append('west', options.bounds.west.toString());
  }

  // Pagination - default to larger page size for maps
  params.append('page', (options.page || 1).toString());
  params.append('pageSize', (options.pageSize || 100).toString());

  // Filtering options - use the proper parameter names that the backend expects
  if (options.showAvailable !== undefined) {
    params.append('showAvailable', options.showAvailable.toString());
  }
  if (options.showUnderContract !== undefined) {
    params.append('showUnderContract', options.showUnderContract.toString());
  }
  if (options.showSold !== undefined) {
    params.append('showSold', options.showSold.toString());
  }

  // Call the API endpoint
  return fetchFromAPI<Property[]>(`/v1/properties/map?${params.toString()}`);
}

/**
 * Progress callback for geocoding operations
 */
export interface GeocodingProgressCallback {
  (property: Property, status: string, details?: string): void;
}

/**
 * Geocode properties with missing coordinates
 * 
 * @param propertyIds Array of property IDs to geocode
 * @param progressCallback Optional callback to report progress
 * @returns Promise resolving to geocoded properties
 */
export async function geocodeProperties(
  properties: Property[] | string[], 
  progressCallback?: GeocodingProgressCallback
): Promise<Property[]> {
  // Convert property objects to IDs if needed
  const propertyIds = properties.map(p => typeof p === 'string' ? p : p.id);
  
  try {
    // Make the API call
    const result = await fetchFromAPI<Property[]>('/v1/properties/geocode', {
      method: 'POST',
      body: JSON.stringify({ propertyIds })
    });
    
    // If there's a progress callback, call it for each property
    if (progressCallback && result) {
      result.forEach(property => {
        progressCallback(property, 'success', 'Geocoded successfully');
      });
    }
    
    return result;
  } catch (error: any) {
    // If there's a progress callback, call it with the error
    if (progressCallback) {
      properties.forEach(p => {
        const property = typeof p === 'string' 
          ? { id: p } as Property 
          : p;
        progressCallback(property, 'error', error.message || 'Geocoding failed');
      });
    }
    throw error;
  }
}

/**
 * Clean property data (fix formatting issues, etc)
 * 
 * @param propertyIds Array of property IDs to clean
 * @returns Promise resolving to cleaned properties
 */
export async function cleanProperties(propertyIds: string[]): Promise<Property[]> {
  return fetchFromAPI<Property[]>('/v1/properties/clean', {
    method: 'POST',
    body: JSON.stringify({ propertyIds })
  });
}

/**
 * Run property analysis to find patterns and issues
 * 
 * @param propertyIds Array of property IDs to analyze
 * @returns Promise resolving to analysis results
 */
export async function analyzeProperties(propertyIds: string[]): Promise<any> {
  return fetchFromAPI<any>('/v1/properties/analyze', {
    method: 'POST',
    body: JSON.stringify({ propertyIds })
  });
} 