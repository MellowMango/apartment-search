/**
 * Supabase client for frontend operations
 */
import { createClient } from '@supabase/supabase-js';
import { Property, PropertySearchParams } from '../types/property';

// Get Supabase credentials from environment variables
const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL;
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;

if (!supabaseUrl || !supabaseAnonKey) {
  console.error(
    'Supabase credentials not found. Please set NEXT_PUBLIC_SUPABASE_URL and NEXT_PUBLIC_SUPABASE_ANON_KEY environment variables.'
  );
}

// Create Supabase client
export const supabase = createClient(supabaseUrl || '', supabaseAnonKey || '', {
  auth: {
    autoRefreshToken: true,
    persistSession: true,
    detectSessionInUrl: true
  }
});

/**
 * Get the current authenticated user
 * @returns {Promise<Object|null>} The user object or null if not authenticated
 */
export const getCurrentUser = async () => {
  const { data: { user } } = await supabase.auth.getUser();
  return user;
};

/**
 * Sign up a new user
 * @param {string} email - User's email
 * @param {string} password - User's password
 * @returns {Promise<Object>} The result of the sign up operation
 */
export const signUp = async (email: string, password: string) => {
  return await supabase.auth.signUp({
    email,
    password,
  });
};

/**
 * Sign in a user
 * @param {string} email - User's email
 * @param {string} password - User's password
 * @returns {Promise<Object>} The result of the sign in operation
 */
export const signIn = async (email: string, password: string) => {
  return await supabase.auth.signInWithPassword({
    email,
    password,
  });
};

/**
 * Sign out the current user
 * @returns {Promise<Object>} The result of the sign out operation
 */
export const signOut = async () => {
  return await supabase.auth.signOut();
};

interface FetchPropertiesOptions {
  filters?: Record<string, any>;
  page?: number;
  pageSize?: number;
  sortBy?: string;
  sortAsc?: boolean;
  includeIncomplete?: boolean;
  includeResearch?: boolean;
  noLimit?: boolean;
  bounds?: {
    north: number;
    south: number;
    east: number;
    west: number;
  } | Record<string, never>;
}

/**
 * Fetch properties from Supabase with enhanced error handling and data normalization
 * 
 * @param {Object} options - Query options
 * @returns {Promise<Array>} Array of normalized properties
 */
export const fetchProperties = async (options: FetchPropertiesOptions = {}): Promise<Property[]> => {
  console.log('Fetching properties with options:', JSON.stringify(options, null, 2));
  
  // Check if we should join with research data
  if (options.includeResearch !== false) {
    // Include research data in our query - we'll join with property_research table
    try {
      // Start with a query that joins properties with research data
      let query = supabase.from('properties')
        .select(`
          *,
          property_research:property_research(*)
        `);
      
      // Apply filters if provided
      if (options.filters) {
        Object.entries(options.filters).forEach(([key, value]) => {
          if (value !== undefined && value !== null && value !== '') {
            // Handle special filter syntax
            if (key === 'or') {
              query = query.or(value);
            } else if (key.endsWith('_gte')) {
              const actualKey = key.replace('_gte', '');
              query = query.gte(actualKey, value);
            } else if (key.endsWith('_lte')) {
              const actualKey = key.replace('_lte', '');
              query = query.lte(actualKey, value);
            } else if (key.endsWith('_gt')) {
              const actualKey = key.replace('_gt', '');
              query = query.gt(actualKey, value);
            } else if (key.endsWith('_lt')) {
              const actualKey = key.replace('_lt', '');
              query = query.lt(actualKey, value);
            } else if (key.endsWith('_ilike')) {
              const actualKey = key.replace('_ilike', '');
              query = query.ilike(actualKey, value);
            } else {
              // Default to equality matching
              query = query.eq(key, value);
            }
          }
        });
      }
      
      // Apply geographical bounds if provided to limit to visible area
      if (options.bounds) {
        const { north, south, east, west } = options.bounds;
        
        if (north && south && east && west) {
          // Only get properties within the current map bounds
          query = query
            .gte('latitude', south)
            .lte('latitude', north)
            .gte('longitude', west)
            .lte('longitude', east);
          
          console.log(`Applying geographical bounds filter: lat ${south}-${north}, lng ${west}-${east}`);
        }
      }
      
      // If we need complete properties with coordinates for the map
      if (!options.includeIncomplete) {
        // Use a more precise filter to avoid empty/zero coordinates
        // First prioritize properties with valid coordinates (either direct or from research)
        query = query
          .not('latitude', 'is', null)
          .not('longitude', 'is', null)
          .not('latitude', 'eq', 0)
          .not('longitude', 'eq', 0)
          .order('created_at', { ascending: false });
        
        console.log('Querying for properties with valid coordinates only');
      } else {
        console.log('Including all properties regardless of coordinates');
      }
      
      // Apply pagination unless noLimit is set to true
      if (!options.noLimit && options.page && options.pageSize) {
        const start = (options.page - 1) * options.pageSize;
        const end = start + options.pageSize - 1;
        query = query.range(start, end);
        console.log(`Applying pagination: range ${start}-${end}`);
      } else if (options.noLimit) {
        // When loading all properties, we'll limit to 2500 max for performance
        // This should be enough for the entire dataset
        query = query.limit(2500);
        console.log('Loading up to 2500 properties (bypassing pagination)');
      }
      
      // Apply sorting
      if (options.sortBy) {
        query = query.order(options.sortBy, { ascending: options.sortAsc !== false });
      }
      
      // Execute query
      console.log('Executing Supabase query...');
      const { data, error } = await query;
      
      if (error) {
        // If this fails, we'll fall back to the non-join query
        console.warn('Error fetching properties with research join:', error);
        // Continue to fallback query below
      } else if (data && data.length > 0) {
        console.log(`Found ${data.length} properties with research data`);
        
        // Merge research data with property data
        const normalizedProperties = data.map(property => {
          // Extract research data if available
          const researchData = property.property_research && property.property_research.length > 0 
            ? property.property_research[0] 
            : null;
          
          // Delete the nested property_research to avoid confusion
          delete property.property_research;
          
          // Normalize the property
          const normalizedProperty = normalizeProperty(property);
          
          // If we have research data with valid coordinates, use them
          if (researchData && researchData.modules) {
            try {
              // Check for valid coordinates in property_details module
              const propertyDetails = researchData.modules.property_details || {};
              
              // Only use research coordinates if they're valid and property doesn't have them
              if (propertyDetails.latitude && propertyDetails.longitude &&
                  typeof propertyDetails.latitude === 'number' && 
                  typeof propertyDetails.longitude === 'number' &&
                  !normalizedProperty._is_grid_pattern) {
                
                normalizedProperty.latitude = propertyDetails.latitude;
                normalizedProperty.longitude = propertyDetails.longitude;
                normalizedProperty._coordinates_from_research = true;
                normalizedProperty._coordinates_missing = false;
                normalizedProperty._needs_geocoding = false;
                
                console.log(`Using research coordinates for property ${property.id}: [${propertyDetails.latitude}, ${propertyDetails.longitude}]`);
              }
              
              // Add research data to property
              normalizedProperty._research = {
                depth: researchData.research_depth,
                date: researchData.research_date,
                summary: researchData.executive_summary
              };
            } catch (e) {
              console.error('Error processing research data:', e);
            }
          }
          
          return normalizedProperty;
        });
        
        // For map view, filter out properties without valid coordinates
        if (!options.includeIncomplete) {
          const propertiesWithCoordinates = normalizedProperties.filter(
            p => p.latitude && p.longitude && 
                (p._coordinates_from_research || 
                  (!p._coordinates_missing && !p._is_grid_pattern))
          );
          
          console.log(`Filtered to ${propertiesWithCoordinates.length} properties with valid coordinates`);
          
          if (propertiesWithCoordinates.length > 0) {
            return propertiesWithCoordinates;
          }
          
          // If all properties were filtered out, return them anyway to avoid empty map
          console.warn('All properties were filtered out due to missing coordinates');
        }
        
        return normalizedProperties;
      }
    } catch (err) {
      console.error('Error in join query:', err);
      // Continue to fallback query
    }
  }
  
  // Fallback to a simpler query without joins if the join query failed
  try {
    console.log('Executing fallback query...');
    let query = supabase.from('properties').select('*');
    
    // Apply filters if provided
    if (options.filters) {
      Object.entries(options.filters).forEach(([key, value]) => {
        if (value !== undefined && value !== null && value !== '') {
          // Same filtering logic as above
          if (key === 'or') {
            query = query.or(value);
          } else if (key.endsWith('_gte')) {
            const actualKey = key.replace('_gte', '');
            query = query.gte(actualKey, value);
          } else if (key.endsWith('_lte')) {
            const actualKey = key.replace('_lte', '');
            query = query.lte(actualKey, value);
          } else if (key.endsWith('_gt')) {
            const actualKey = key.replace('_gt', '');
            query = query.gt(actualKey, value);
          } else if (key.endsWith('_lt')) {
            const actualKey = key.replace('_lt', '');
            query = query.lt(actualKey, value);
          } else if (key.endsWith('_ilike')) {
            const actualKey = key.replace('_ilike', '');
            query = query.ilike(actualKey, value);
          } else {
            query = query.eq(key, value);
          }
        }
      });
    }
    
    // Apply geographical bounds if provided
    if (options.bounds) {
      const { north, south, east, west } = options.bounds;
      
      if (north && south && east && west) {
        query = query
          .gte('latitude', south)
          .lte('latitude', north)
          .gte('longitude', west)
          .lte('longitude', east);
      }
    }
    
    // Apply sorting
    if (options.sortBy) {
      query = query.order(options.sortBy, { ascending: options.sortAsc !== false });
    } else {
      query = query.order('created_at', { ascending: false });
    }
    
    // Apply pagination
    if (!options.noLimit && options.page && options.pageSize) {
      const start = (options.page - 1) * options.pageSize;
      const end = start + options.pageSize - 1;
      query = query.range(start, end);
    } else if (options.noLimit) {
      query = query.limit(2500);
    }
    
    // Execute query
    const { data, error } = await query;
    
    if (error) {
      console.error('Error fetching properties:', error);
      return [];
    }
    
    // Normalize properties
    const normalizedProperties = data.map(normalizeProperty);
    
    // Filter out invalid coordinates for map view
    if (!options.includeIncomplete) {
      const validProperties = normalizedProperties.filter(
        p => p.latitude && p.longitude && typeof p.latitude === 'number' && typeof p.longitude === 'number'
      );
      
      console.log(`Filtered to ${validProperties.length} properties with valid coordinates`);
      return validProperties;
    }
    
    return normalizedProperties;
  } catch (error) {
    console.error('Error executing fallback query:', error);
    return [];
  }
};

/**
 * Normalize property data by processing coordinates and other fields
 * 
 * @param {Object} property - Raw property data from Supabase
 * @returns {Object} - Normalized property object
 */
const normalizeProperty = (property: any): Property => {
  const normalizedProperty: Property = { ...property };
  
  // Convert coordinates to numbers if they're strings
  if (property.latitude && typeof property.latitude === 'string') {
    normalizedProperty.latitude = parseFloat(property.latitude);
  }
  
  if (property.longitude && typeof property.longitude === 'string') {
    normalizedProperty.longitude = parseFloat(property.longitude);
  }
  
  // Flag properties with missing coordinates
  if (!property.latitude || !property.longitude) {
    normalizedProperty._coordinates_missing = true;
    normalizedProperty._needs_geocoding = true;
  }
  
  // Flag properties with zero coordinates
  if (property.latitude === 0 && property.longitude === 0) {
    normalizedProperty._is_grid_pattern = true;
    normalizedProperty._needs_geocoding = true;
  }
  
  // Flag test properties
  if (isTestProperty(property)) {
    normalizedProperty._is_test_property = true;
  }
  
  return normalizedProperty;
};

/**
 * Check if a property is a test property
 * 
 * @param {Object} property - Property object
 * @returns {boolean} - True if it's a test property
 */
const isTestProperty = (property: any): boolean => {
  const testPatterns = [
    /test/i,
    /dummy/i,
    /example/i,
    /sample/i,
    /fake/i
  ];
  
  // Check if any test pattern matches the property name
  const nameMatches = property.name && testPatterns.some(pattern => pattern.test(property.name));
  
  // Check if any test pattern matches the property address
  const addressMatches = property.address && testPatterns.some(pattern => pattern.test(property.address));
  
  // If it's explicitly marked as a test property
  const explicitlyMarked = property._is_test_property === true;
  
  return nameMatches || addressMatches || explicitlyMarked;
};

/**
 * Create a test property for development and testing
 * 
 * @returns {Promise<Object>} - The created property
 */
export const createTestProperty = async (): Promise<Property> => {
  // Generate a random Austin area location
  const centerLat = 30.2672;
  const centerLng = -97.7431;
  const radiusDeg = 0.03;
  
  const randomLat = centerLat + (Math.random() * 2 - 1) * radiusDeg;
  const randomLng = centerLng + (Math.random() * 2 - 1) * radiusDeg;
  
  // Create a test property object
  const testProperty = {
    name: `Test Property ${Math.floor(Math.random() * 1000)}`,
    address: `${1000 + Math.floor(Math.random() * 9000)} Test St`,
    city: 'Austin',
    state: 'TX',
    zip: '78701',
    price: 1000000 + Math.floor(Math.random() * 9000000),
    units: 5 + Math.floor(Math.random() * 50),
    year_built: 1980 + Math.floor(Math.random() * 40),
    status: ['For Sale', 'Under Contract', 'Sold'][Math.floor(Math.random() * 3)],
    latitude: randomLat,
    longitude: randomLng,
    broker: 'Test Broker',
    _is_test_property: true,
    created_at: new Date().toISOString()
  };
  
  // Insert the test property into the database
  const { data, error } = await supabase.from('properties').insert([testProperty]).select();
  
  if (error) {
    console.error('Error creating test property:', error);
    throw error;
  }
  
  console.log('Created test property:', data[0]);
  return data[0] as Property;
}; 