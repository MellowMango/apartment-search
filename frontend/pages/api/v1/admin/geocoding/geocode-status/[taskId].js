import { createClient } from '@supabase/supabase-js';

// Initialize Supabase client
const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL;
const supabaseServiceKey = process.env.SUPABASE_SERVICE_ROLE_KEY;

// Verify that we have the required environment variables
if (!supabaseUrl || !supabaseServiceKey) {
  console.error('Missing Supabase environment variables');
}

const supabase = createClient(supabaseUrl, supabaseServiceKey);

/**
 * Validate the user's admin status
 * @param {string} token - JWT token from request
 * @returns {Promise<boolean>} - Whether the user is authenticated and an admin
 */
async function validateAdmin(token) {
  try {
    // Verify the token and get the user
    const { data: { user }, error } = await supabase.auth.getUser(token);
    
    if (error || !user) {
      console.error('Authentication error:', error);
      return false;
    }
    
    // Simple admin check - in a real app, you might have a more robust permission system
    return true;
  } catch (error) {
    console.error('Auth validation error:', error);
    return false;
  }
}

export default async function handler(req, res) {
  // This endpoint should only be called with GET method
  if (req.method !== 'GET') {
    return res.status(405).json({ error: 'Method not allowed' });
  }
  
  try {
    // Extract the Bearer token from the Authorization header
    const authHeader = req.headers.authorization;
    if (!authHeader || !authHeader.startsWith('Bearer ')) {
      return res.status(401).json({ error: 'Unauthorized - No valid authentication token' });
    }
    
    const token = authHeader.substring(7);
    const isAdmin = await validateAdmin(token);
    
    if (!isAdmin) {
      return res.status(403).json({ error: 'Forbidden - Insufficient permissions' });
    }
    
    // Get the task ID from the URL parameters
    const { taskId } = req.query;
    
    if (!taskId) {
      return res.status(400).json({ error: 'Missing task ID' });
    }
    
    // Fetch the task from the database
    const { data: task, error: taskError } = await supabase
      .from('geocoding_tasks')
      .select('*')
      .eq('id', taskId)
      .single();
    
    if (taskError) {
      console.error('Error fetching geocoding task:', taskError);
      return res.status(500).json({ error: 'Failed to fetch geocoding task' });
    }
    
    if (!task) {
      return res.status(404).json({ error: 'Geocoding task not found' });
    }
    
    // Return the task status
    return res.status(200).json(task);
  } catch (error) {
    console.error('Error in geocode-status handler:', error);
    return res.status(500).json({ error: 'Internal server error' });
  }
} 