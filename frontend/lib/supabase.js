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
export const supabase = createClient(supabaseUrl, supabaseAnonKey);

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
 * Fetch properties from Supabase
 * @param {Object} options - Query options
 * @returns {Promise<Array>} Array of properties
 */
export const fetchProperties = async (options = {}) => {
  let query = supabase.from('properties').select('*');
  
  // Apply filters if provided
  if (options.filters) {
    Object.entries(options.filters).forEach(([key, value]) => {
      if (value !== undefined && value !== null && value !== '') {
        query = query.eq(key, value);
      }
    });
  }
  
  // Apply pagination
  if (options.page && options.pageSize) {
    const start = (options.page - 1) * options.pageSize;
    const end = start + options.pageSize - 1;
    query = query.range(start, end);
  }
  
  // Apply sorting
  if (options.sortBy) {
    query = query.order(options.sortBy, { ascending: options.sortAsc !== false });
  }
  
  const { data, error } = await query;
  
  if (error) {
    console.error('Error fetching properties:', error);
    throw error;
  }
  
  return data;
};

export default supabase; 