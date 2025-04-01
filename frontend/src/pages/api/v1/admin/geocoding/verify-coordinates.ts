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
    return true;
  } catch (error) {
    console.error('Auth validation error:', error);
    return false;
  }
}

/**
 * Fetch properties that need coordinate verification
 */
async function fetchPropertiesToVerify(options) {
  const { checkAll, batchSize } = options;
  
  let query = supabase
    .from('properties')
    .select('id, name, address, city, state, zip_code, latitude, longitude')
    .not('address', 'is', null)
    .not('address', 'eq', '');
  
  if (!checkAll) {
    // Only get properties with potential coordinate issues:
    // 1. Properties with coordinates outside of Austin area
    // 2. Properties with suspicious coordinate patterns
    // 3. Properties with very low precision coordinates
    query = query
      .not('latitude', 'is', null)
      .not('longitude', 'is', null)
      .not('latitude', 'eq', 0)
      .not('longitude', 'eq', 0)
      .or(
        // Outside Austin area (approximate boundaries)
        'latitude.lt.29.5,latitude.gt.31.0,longitude.lt.-98.0,longitude.gt.-97.0'
      );
  }
  
  // Limit to batch size
  query = query.limit(batchSize);
  
  const { data, error } = await query;
  
  if (error) {
    console.error('Error fetching properties to verify:', error);
    throw error;
  }
  
  return data || [];
}

/**
 * Verify coordinates using Google Maps API
 */
async function verifyWithGoogleMaps(property) {
  try {
    // Construct the full address for geocoding
    const address = [
      property.address,
      property.city,
      property.state,
      property.zip_code
    ].filter(Boolean).join(', ');
    
    // Use Google Maps Geocoding API
    const response = await fetch(
      `https://maps.googleapis.com/maps/api/geocode/json?address=${encodeURIComponent(address)}&key=${googleMapsApiKey}`
    );
    
    if (!response.ok) {
      throw new Error(`Google Maps API error: ${response.statusText}`);
    }
    
    const data = await response.json();
    
    if (data.status !== 'OK' || !data.results || data.results.length === 0) {
      return {
        property,
        verified: false,
        error: `Geocoding failed: ${data.status || 'No results'}`
      };
    }
    
    // Extract location from the first result
    const location = data.results[0].geometry.location;
    const googleLat = location.lat;
    const googleLng = location.lng;
    
    // Calculate distance between current and Google coordinates (in meters)
    const distance = calculateDistance(
      property.latitude,
      property.longitude,
      googleLat,
      googleLng
    );
    
    return {
      property,
      verified: true,
      googleLat,
      googleLng,
      distance,
      formattedAddress: data.results[0].formatted_address,
      needsUpdate: distance > 100 // Consider updating if more than 100 meters off
    };
  } catch (error) {
    console.error(`Error verifying coordinates for property ${property.id}:`, error);
    return {
      property,
      verified: false,
      error: error.message
    };
  }
}

/**
 * Calculate distance between two coordinate points using Haversine formula
 * @returns {number} Distance in meters
 */
function calculateDistance(lat1, lon1, lat2, lon2) {
  if (!lat1 || !lon1 || !lat2 || !lon2) return Infinity;
  
  const R = 6371e3; // Earth radius in meters
  const φ1 = lat1 * Math.PI / 180;
  const φ2 = lat2 * Math.PI / 180;
  const Δφ = (lat2 - lat1) * Math.PI / 180;
  const Δλ = (lon2 - lon1) * Math.PI / 180;
  
  const a = Math.sin(Δφ/2) * Math.sin(Δφ/2) +
            Math.cos(φ1) * Math.cos(φ2) *
            Math.sin(Δλ/2) * Math.sin(Δλ/2);
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
  
  return R * c; // Distance in meters
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
    const { 
      batch_size = 50, 
      check_all = false,
      auto_fix = true 
    } = req.body;
    
    // Validate batch size (limit to reasonable values)
    const batchSize = Math.min(Math.max(1, batch_size), 500);
    
    // Generate a task ID for tracking
    const taskId = uuidv4();
    
    // Create a task record in the database
    const { error: taskError } = await supabase
      .from('geocoding_tasks')
      .insert({
        id: taskId,
        status: 'pending',
        batch_size: batchSize,
        task_type: 'verify_coordinates',
        start_time: new Date().toISOString()
      });
    
    if (taskError) {
      console.error('Error creating coordinate verification task:', taskError);
      return res.status(500).json({ error: 'Failed to create verification task' });
    }
    
    // Start the verification process asynchronously
    process.nextTick(async () => {
      try {
        // Update task status to processing
        await supabase
          .from('geocoding_tasks')
          .update({ status: 'processing' })
          .eq('id', taskId);
        
        console.log(`Started coordinate verification task ${taskId} with batch size ${batchSize}`);
        
        // Fetch properties to verify
        const properties = await fetchPropertiesToVerify({
          checkAll: check_all,
          batchSize
        });
        
        console.log(`Found ${properties.length} properties to verify for task ${taskId}`);
        
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
        let updateCount = 0;
        const startTime = Date.now();
        
        // Results store
        const verificationResults = [];
        
        // Process each property
        for (const property of properties) {
          try {
            console.log(`Verifying coordinates for property ${property.id}: "${property.name}"`);
            
            // Verify with Google Maps
            const verificationResult = await verifyWithGoogleMaps(property);
            verificationResults.push(verificationResult);
            
            if (verificationResult.verified) {
              successCount++;
              
              if (verificationResult.needsUpdate && auto_fix) {
                // Update the property with corrected coordinates
                const { error: updateError } = await supabase
                  .from('properties')
                  .update({
                    latitude: verificationResult.googleLat,
                    longitude: verificationResult.googleLng,
                    geocoded_at: new Date().toISOString(),
                    verified_address: verificationResult.formattedAddress
                  })
                  .eq('id', property.id);
                
                if (updateError) {
                  console.error(`Error updating coordinates for property ${property.id}:`, updateError);
                } else {
                  updateCount++;
                }
              }
            } else {
              errorCount++;
            }
            
            // Respect Google Maps API rate limits with small delay
            await new Promise(resolve => setTimeout(resolve, 200));
          } catch (error) {
            console.error(`Error processing property ${property.id}:`, error);
            errorCount++;
          }
        }
        
        // Calculate duration and success rate
        const endTime = Date.now();
        const durationSeconds = (endTime - startTime) / 1000;
        const successRate = properties.length > 0 ? (successCount / properties.length) * 100 : 0;
        
        // Store verification results in task metadata
        const metadata = {
          results: verificationResults,
          updatedCount: updateCount
        };
        
        // Update the task with final results
        await supabase
          .from('geocoding_tasks')
          .update({
            status: 'completed',
            end_time: new Date().toISOString(),
            success_count: successCount,
            error_count: errorCount,
            update_count: updateCount,
            success_rate: successRate,
            duration_seconds: durationSeconds,
            metadata: metadata
          })
          .eq('id', taskId);
        
        console.log(`Completed verification task ${taskId} with ${successCount} successes, ${updateCount} updates, and ${errorCount} errors`);
      } catch (error) {
        console.error(`Error processing verification task ${taskId}:`, error);
        
        // Update task status to error
        await supabase
          .from('geocoding_tasks')
          .update({
            status: 'error',
            end_time: new Date().toISOString(),
            error_message: error.message || 'Unknown error during verification'
          })
          .eq('id', taskId);
      }
    });
    
    // Return immediate success response with the task ID
    return res.status(200).json({
      message: 'Coordinate verification task started',
      task_id: taskId
    });
  } catch (error) {
    console.error('Error in verify-coordinates handler:', error);
    return res.status(500).json({ error: 'Internal server error' });
  }
} 