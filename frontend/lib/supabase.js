/**
 * Supabase client for frontend operations
 */
import { createClient } from '@supabase/supabase-js';

// Get Supabase credentials from environment variables
const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL;
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;

if (!supabaseUrl || !supabaseAnonKey) {
  console.error(
    'Supabase credentials not found. Please set NEXT_PUBLIC_SUPABASE_URL and NEXT_PUBLIC_SUPABASE_ANON_KEY environment variables.'
  );
}

// Create Supabase client
export const supabase = createClient(supabaseUrl, supabaseAnonKey, {
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
export const signUp = async (email, password) => {
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
export const signIn = async (email, password) => {
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

/**
 * Fetch properties from Supabase with enhanced error handling and data normalization
 * 
 * @param {Object} options - Query options
 * @param {Object} options.filters - Key-value pairs for filtering (e.g. {status: 'For Sale'})
 * @param {number} options.page - Page number for pagination
 * @param {number} options.pageSize - Number of items per page
 * @param {string} options.sortBy - Field to sort by
 * @param {boolean} options.sortAsc - Sort in ascending order if true
 * @param {boolean} options.includeIncomplete - Whether to include properties with missing coordinates
 * @param {boolean} options.includeResearch - Whether to include enriched research data
 * @param {boolean} options.noLimit - Whether to bypass pagination limits and get all properties
 * @param {Object} options.bounds - Geographical bounds to filter properties (north, south, east, west)
 * @returns {Promise<Array>} Array of normalized properties
 */
export const fetchProperties = async (options = {}) => {
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
          console.warn('All properties were filtered out for having invalid coordinates');
        }
        
        return normalizedProperties;
      }
    } catch (joinError) {
      console.error('Error with research join query:', joinError);
      // Fall back to standard query
    }
  }
  
  // Fallback - standard query without research data
  console.log('Using standard property query without research data');
  let query = supabase.from('properties').select('*');
  
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
  
  // Apply geographical bounds if provided
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
    console.error('Error fetching properties:', error);
    throw error;
  }
  
  if (!data || data.length === 0) {
    console.warn('No properties found with the given criteria');
    return [];
  }
  
  console.log(`Fetched ${data.length} properties successfully`);
  
  // Normalize property data to handle inconsistencies
  return data.map(property => normalizeProperty(property));
};

/**
 * Normalizes property data to handle inconsistent field names
 * 
 * @param {Object} property - Raw property data from Supabase
 * @returns {Object} Normalized property data
 */
const normalizeProperty = (property) => {
  // Make copy to avoid mutating the original
  const normalized = { ...property };
  
  // Handle inconsistent unit field names
  normalized.units = property.num_units || property.units || null;
  
  // Use property name or derive from address if missing
  if (!normalized.name || normalized.name.trim() === '') {
    normalized.name = property.address 
      ? `Property at ${property.address.split(',')[0]}`
      : `Property ${property.id.substring(0, 8)}`;
  }
  
  // Make sure we have status
  normalized.status = property.status || property.property_status || 'Listed';
  
  // Check if this is likely a test property
  normalized._is_test_property = isTestProperty(property);
  
  // Add coordinate related flags
  if (property.latitude && property.longitude &&
      typeof property.latitude === 'number' && 
      typeof property.longitude === 'number' &&
      !(property.latitude === 0 && property.longitude === 0)) {
    
    // Check if coordinates are valid (in proper lat/long ranges)
    const isValidLatitude = property.latitude >= -90 && property.latitude <= 90;
    const isValidLongitude = property.longitude >= -180 && property.longitude <= 180;
    
    // Austin area boundaries (approximate) - helps detect obviously wrong coordinates
    const isInAustinArea = (
      property.latitude >= 29.5 && property.latitude <= 31.0 && 
      property.longitude >= -98.0 && property.longitude <= -97.0
    );
    
    // Check if coordinates are part of a grid pattern (low precision or suspicious patterns)
    const latStr = String(property.latitude);
    const lngStr = String(property.longitude);
    
    // Only flag very low precision coordinates as suspicious (1 decimal place or less)
    const hasLowPrecision = 
      (latStr.includes('.') && latStr.split('.')[1].length <= 1) ||
      (lngStr.includes('.') && lngStr.split('.')[1].length <= 1);
      
    // Reduced set of suspicious patterns
    const hasSuspiciousPattern = 
      latStr === lngStr || // Same lat/lng is very unlikely
      latStr.endsWith('00000') || 
      lngStr.endsWith('00000');
    
    // Keep track of whether this is detected as a grid pattern
    const isGridPattern = hasLowPrecision || hasSuspiciousPattern;
    
    // Flag coordinates as missing if they're invalid or suspicious
    if (!isValidLatitude || !isValidLongitude || isGridPattern) {
      normalized._coordinates_missing = true;
      normalized._needs_geocoding = true;
      normalized._is_grid_pattern = isGridPattern;
      normalized._is_invalid_range = !isValidLatitude || !isValidLongitude;
      
      // Debug info for invalid coordinates
      if (!isValidLatitude || !isValidLongitude) {
        console.warn(`Invalid coordinate range for property ${property.id}: [${property.latitude}, ${property.longitude}]`);
      }
    } else {
      // Set additional flags for coordinates outside Austin (might be valid but suspicious)
      normalized._outside_austin = !isInAustinArea;
      normalized._coordinates_missing = false;
      normalized._needs_geocoding = false;
    }
  } else {
    // No coordinates or invalid coordinates
    normalized._coordinates_missing = true;
    normalized._needs_geocoding = true;
  }
  
  return normalized;
};

/**
 * Determines if a property is likely a test/example property
 * 
 * @param {Object} property - Property data to check
 * @returns {boolean} True if property is likely a test property
 */
const isTestProperty = (property) => {
  // Check for common test property indicators in name
  const name = (property.name || '').toLowerCase();
  const testIndicators = ['test', 'example', 'sample', 'demo', 'dummy', 'template'];
  
  for (const indicator of testIndicators) {
    if (name.includes(indicator)) {
      return true;
    }
  }
  
  // Check for unrealistic values
  if (property.price === 1) {
    return true;
  }
  
  if (property.units === 0 || property.units === 999 || property.num_units === 0 || property.num_units === 999) {
    return true;
  }
  
  // Check for placeholder addresses
  const address = (property.address || '').toLowerCase();
  const placeholderIndicators = ['123 main', 'test address', 'example', 'placeholder'];
  
  for (const indicator of placeholderIndicators) {
    if (address.includes(indicator)) {
      return true;
    }
  }
  
  return false;
};

/**
 * Creates a test property in the database for testing purposes
 * Use this to verify the database connection is working
 * 
 * @returns {Promise<Object>} The created test property
 */
export const createTestProperty = async () => {
  // First, check if we can get the table structure
  try {
    // Try to get one record to see the schema
    const { data: sampleProperty, error: sampleError } = await supabase
      .from('properties')
      .select('*')
      .limit(1);
    
    // Basic test property that matches the schema from supabase-setup.md
    const baseTestProperty = {
      name: `Test Property ${new Date().toISOString().slice(0, 16)}`,
      address: '123 Test Street',
      city: 'Austin',
      state: 'TX',
      zip_code: '78701',
      latitude: 30.2672,
      longitude: -97.7431,
      price: 5000000,
      units: 50,
      year_built: 2010,
      property_type: 'MULTIFAMILY',
      status: 'available', // Use status rather than property_status from the docs
      description: 'This is a test property created to verify database connectivity.',
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString()
    };
    
    // If we have a sample, adapt to its schema
    let testProperty = baseTestProperty;
    if (!sampleError && sampleProperty && sampleProperty.length > 0) {
      console.log('Found existing property for schema reference:', sampleProperty[0]);
      
      // Adapt our test property to match the existing schema
      const sample = sampleProperty[0];
      
      // Create a new object with only the fields that exist in the sample
      const adaptedProperty = {};
      Object.keys(baseTestProperty).forEach(key => {
        // If the field exists in the sample, use our test value
        if (key in sample) {
          adaptedProperty[key] = baseTestProperty[key];
        }
      });
      
      // Check key fields that might have different names
      if ('property_status' in sample && !('status' in sample)) {
        adaptedProperty.property_status = baseTestProperty.status;
        delete adaptedProperty.status;
      }
      
      if ('num_units' in sample && !('units' in sample)) {
        adaptedProperty.num_units = baseTestProperty.units;
        delete adaptedProperty.units;
      }
      
      // Use the adapted property
      testProperty = adaptedProperty;
      console.log('Adapted test property to match schema:', testProperty);
    } else {
      console.log('No sample property found, using default schema');
    }
    
    // Try to insert the test property
    const { data, error } = await supabase
      .from('properties')
      .insert(testProperty)
      .select();
      
    if (error) {
      console.error('Error creating test property:', error);
      
      // Try again with minimal fields if this failed
      if (error.message && (error.message.includes('violates not-null constraint') || 
                           error.message.includes('missing'))) {
        console.log('Trying again with minimal required fields');
        
        // Try with just the bare minimum fields
        const minimalProperty = {
          name: `Test Property ${new Date().toISOString().slice(0, 16)}`,
          address: '123 Test Street',
          city: 'Austin',
          state: 'TX'
        };
        
        const { data: minData, error: minError } = await supabase
          .from('properties')
          .insert(minimalProperty)
          .select();
          
        if (minError) {
          console.error('Error creating minimal property:', minError);
          throw minError;
        }
        
        console.log('Successfully created minimal test property:', minData);
        return {
          data: minData,
          info: 'Created with minimal fields only'
        };
      }
      
      throw error;
    }
    
    console.log('Test property created:', data);
    return {
      data,
      info: 'Created with full fields'
    };
  } catch (err) {
    console.error('Error in createTestProperty:', err);
    throw err;
  }
};

export default supabase; 