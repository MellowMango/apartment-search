import { createClient } from '@supabase/supabase-js';
import { v4 as uuidv4 } from 'uuid';

// Initialize Supabase client
const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL;
const supabaseServiceKey = process.env.SUPABASE_SERVICE_ROLE_KEY;
const googleMapsApiKey = process.env.GOOGLE_MAPS_API_KEY;

// Verify that we have the required environment variables
if (!supabaseUrl || !supabaseServiceKey) {
  console.error('Missing Supabase environment variables');
}

if (!googleMapsApiKey) {
  console.error('Missing Google Maps API key');
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
    // For now, we'll consider any authenticated user as an admin
    return true;
  } catch (error) {
    console.error('Auth validation error:', error);
    return false;
  }
}

export default async function handler(req, res) {
  // This endpoint should only be called with POST method
  if (req.method !== 'POST') {
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
    
    // Parse the request body
    const { batch_size = 50, force_refresh = false } = req.body;
    
    // Validate batch size (limit to reasonable values)
    const validatedBatchSize = Math.min(Math.max(1, batch_size), 1000);
    
    // Generate a task ID for tracking
    const taskId = uuidv4();
    
    // Create a task record in the database
    const { error: taskError } = await supabase
      .from('geocoding_tasks')
      .insert({
        id: taskId,
        status: 'pending',
        batch_size: validatedBatchSize,
        force_refresh: force_refresh,
        start_time: new Date().toISOString()
      });
    
    if (taskError) {
      console.error('Error creating geocoding task:', taskError);
      return res.status(500).json({ error: 'Failed to create geocoding task' });
    }
    
    // Trigger the actual geocoding process
    // In a production environment, this would typically be handled by a background worker
    // For simplicity, we'll start it asynchronously here and not wait for completion
    process.nextTick(async () => {
      try {
        // Update task status to processing
        await supabase
          .from('geocoding_tasks')
          .update({ status: 'processing' })
          .eq('id', taskId);
        
        console.log(`Started geocoding task ${taskId} with batch size ${validatedBatchSize}`);
        
        // Query for properties that need geocoding
        const query = supabase
          .from('properties')
          .select('id, address, city, state, zip_code')
          .is('latitude', null);
        
        // Apply force refresh filter if needed
        if (!force_refresh) {
          query.or('latitude.is.null,latitude.eq.0');
        }
        
        // Limit to the batch size
        query.limit(validatedBatchSize);
        
        const { data: properties, error: propertiesError } = await query;
        
        if (propertiesError) {
          console.error('Error fetching properties for geocoding:', propertiesError);
          await supabase
            .from('geocoding_tasks')
            .update({ 
              status: 'error', 
              end_time: new Date().toISOString(),
              error_message: 'Failed to fetch properties for geocoding'
            })
            .eq('id', taskId);
          return;
        }
        
        console.log(`Found ${properties.length} properties to geocode for task ${taskId}`);
        
        // Update the task with the number of properties found
        await supabase
          .from('geocoding_tasks')
          .update({ properties_processed: properties.length })
          .eq('id', taskId);
        
        if (properties.length === 0) {
          await supabase
            .from('geocoding_tasks')
            .update({ 
              status: 'completed', 
              end_time: new Date().toISOString(),
              success_count: 0,
              error_count: 0,
              success_rate: 0,
              duration_seconds: 0
            })
            .eq('id', taskId);
          return;
        }
        
        // Track success and error counts
        let successCount = 0;
        let errorCount = 0;
        const startTime = Date.now();
        
        // Process each property (in a real app, consider using a queue system)
        for (const property of properties) {
          try {
            // Only attempt geocoding if we have an address
            if (!property.address) {
              errorCount++;
              continue;
            }
            
            // Construct the full address for geocoding
            const address = [
              property.address,
              property.city,
              property.state,
              property.zip_code
            ].filter(Boolean).join(', ');
            
            // Use Google Maps API instead of Nominatim for more reliable geocoding
            const geocodeUrl = `https://maps.googleapis.com/maps/api/geocode/json?address=${encodeURIComponent(address)}&key=${googleMapsApiKey}`;
            
            // Google Maps API has higher rate limits than Nominatim, but still add a small delay
            await new Promise(resolve => setTimeout(resolve, 200));
            
            const response = await fetch(geocodeUrl);
            
            if (!response.ok) {
              throw new Error(`Geocoding error: ${response.statusText}`);
            }
            
            const data = await response.json();
            
            if (data.status === 'OK' && data.results && data.results.length > 0) {
              // We have coordinates!
              const location = data.results[0].geometry.location;
              const lat = location.lat;
              const lng = location.lng;
              
              // Store the formatted address from Google as well
              const formattedAddress = data.results[0].formatted_address;
              
              // Update the property with the coordinates
              const { error: updateError } = await supabase
                .from('properties')
                .update({
                  latitude: parseFloat(lat),
                  longitude: parseFloat(lng),
                  formatted_address: formattedAddress,
                  geocoded_at: new Date().toISOString(),
                  geocode_source: 'google',
                  geocode_verified: true // Since we're using Google directly, mark as verified
                })
                .eq('id', property.id);
              
              if (updateError) {
                console.error(`Error updating property ${property.id} with coordinates:`, updateError);
                errorCount++;
              } else {
                successCount++;
              }
            } else {
              console.warn(`No geocoding results found for property ${property.id}: ${address}`);
              errorCount++;
            }
          } catch (error) {
            console.error(`Error geocoding property ${property.id}:`, error);
            errorCount++;
          }
        }
        
        // Calculate duration and success rate
        const endTime = Date.now();
        const durationSeconds = (endTime - startTime) / 1000;
        const successRate = properties.length > 0 ? (successCount / properties.length) * 100 : 0;
        
        // Update the task with the final results
        await supabase
          .from('geocoding_tasks')
          .update({
            status: 'completed',
            end_time: new Date().toISOString(),
            success_count: successCount,
            error_count: errorCount,
            success_rate: successRate,
            duration_seconds: durationSeconds
          })
          .eq('id', taskId);
        
        console.log(`Completed geocoding task ${taskId} with ${successCount} successes and ${errorCount} errors`);
      } catch (error) {
        console.error(`Error processing geocoding task ${taskId}:`, error);
        
        // Update task status to error
        await supabase
          .from('geocoding_tasks')
          .update({
            status: 'error',
            end_time: new Date().toISOString(),
            error_message: error.message || 'Unknown error during geocoding'
          })
          .eq('id', taskId);
      }
    });
    
    // Return immediate success response with the task ID
    return res.status(200).json({
      message: 'Geocoding task started',
      task_id: taskId
    });
  } catch (error) {
    console.error('Error in geocode-batch handler:', error);
    return res.status(500).json({ error: 'Internal server error' });
  }
} 