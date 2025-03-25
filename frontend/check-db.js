// Simple script to check Supabase database
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

async function checkDatabase() {
  try {
    // Count total properties
    const { count: totalCount, error: countError } = await supabase
      .from('properties')
      .select('*', { count: 'exact', head: true });
      
    if (countError) {
      console.error('Error counting properties:', countError);
      return;
    }
    
    console.log('Total properties in database:', totalCount);
    
    // Count properties with valid coordinates
    const { count: validCount, error: validError } = await supabase
      .from('properties')
      .select('*', { count: 'exact', head: true })
      .not('latitude', 'is', null)
      .not('longitude', 'is', null)
      .not('latitude', 'eq', 0)
      .not('longitude', 'eq', 0);
      
    if (validError) {
      console.error('Error counting valid properties:', validError);
      return;
    }
    
    console.log('Properties with valid coordinates:', validCount);
    
    // Test retrieving 2000 properties to see if there's any limit
    console.log('Attempting to retrieve 2000 properties...');
    const { data, error } = await supabase
      .from('properties')
      .select('id,name,latitude,longitude')
      .range(0, 1999);
      
    if (error) {
      console.error('Error retrieving properties:', error);
      return;
    }
    
    console.log(`Successfully retrieved ${data.length} properties`);
    console.log('First property:', data[0]);
    console.log('Last property:', data[data.length - 1]);
  } catch (err) {
    console.error('Unexpected error:', err);
  }
}

checkDatabase(); 