// Script to debug Supabase data retrieval with and without limits
require('dotenv').config();
const { createClient } = require('@supabase/supabase-js');

// Get Supabase credentials from environment variables
const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL;
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;

if (!supabaseUrl || !supabaseAnonKey) {
  console.error(
    'Supabase credentials not found. Please set NEXT_PUBLIC_SUPABASE_URL and NEXT_PUBLIC_SUPABASE_ANON_KEY environment variables.'
  );
  process.exit(1);
}

// Create Supabase client
const supabase = createClient(supabaseUrl, supabaseAnonKey, {
  auth: {
    autoRefreshToken: true,
    persistSession: true,
    detectSessionInUrl: true
  }
});

// Simulate the fetchProperties function with different options
async function testFetchProperties() {
  try {
    // First, get the total count
    const { count, error: countError } = await supabase
      .from('properties')
      .select('*', { count: 'exact', head: true });

    if (countError) {
      console.error('Error counting total properties:', countError);
      return;
    }

    console.log(`Total properties in database: ${count}`);

    // Count valid coordinates
    const { count: validCount, error: validError } = await supabase
      .from('properties')
      .select('*', { count: 'exact', head: true })
      .not('latitude', 'is', null)
      .not('longitude', 'is', null)
      .not('latitude', 'eq', 0)
      .not('longitude', 'eq', 0);

    if (validError) {
      console.error('Error counting properties with valid coordinates:', validError);
      return;
    }

    console.log(`Properties with valid coordinates: ${validCount}`);

    // Test with pagination
    console.log('\nTesting with pagination (limit 1000):');
    const { data: paginatedData, error: paginatedError } = await supabase
      .from('properties')
      .select('id,name,latitude,longitude')
      .not('latitude', 'is', null)
      .not('longitude', 'is', null)
      .not('latitude', 'eq', 0)
      .not('longitude', 'eq', 0)
      .range(0, 999);

    if (paginatedError) {
      console.error('Error with pagination query:', paginatedError);
    } else {
      console.log(`Retrieved ${paginatedData.length} properties with pagination`);
      
      // Check how many of these properties have valid coordinates
      const validCoordinates = paginatedData.filter(p => 
        typeof p.latitude === 'number' && 
        typeof p.longitude === 'number' &&
        p.latitude !== 0 && 
        p.longitude !== 0
      );
      console.log(`Of those, ${validCoordinates.length} have valid coordinates`);
    }

    // Test without pagination
    console.log('\nTesting without pagination:');
    const { data: allData, error: allError } = await supabase
      .from('properties')
      .select('id,name,latitude,longitude')
      .not('latitude', 'is', null)
      .not('longitude', 'is', null)
      .not('latitude', 'eq', 0)
      .not('longitude', 'eq', 0);

    if (allError) {
      console.error('Error with no-pagination query:', allError);
    } else {
      console.log(`Retrieved ${allData.length} properties without pagination`);
      
      // Check how many of these properties have valid coordinates
      const validCoordinates = allData.filter(p => 
        typeof p.latitude === 'number' && 
        typeof p.longitude === 'number' &&
        p.latitude !== 0 && 
        p.longitude !== 0
      );
      console.log(`Of those, ${validCoordinates.length} have valid coordinates`);
      
      // Check coordinate ranges to see if they're reasonable for Austin
      const austinAreaCoords = validCoordinates.filter(p => 
        p.latitude >= 29.5 && p.latitude <= 31.0 && 
        p.longitude >= -98.0 && p.longitude <= -97.0
      );
      console.log(`Properties with coordinates in Austin area: ${austinAreaCoords.length}`);
    }
  } catch (err) {
    console.error('Unexpected error:', err);
  }
}

// Run the tests
testFetchProperties(); 