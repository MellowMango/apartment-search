// Simple geocoding API endpoint that uses Mapbox API
import axios from 'axios';

// Initialize API key from environment variables
const mapboxToken = process.env.NEXT_PUBLIC_MAPBOX_TOKEN;

if (!mapboxToken) {
  console.error('Missing Mapbox API token');
}

/**
 * Handler for the geocode API endpoint
 */
export default async function handler(req, res) {
  // Only allow GET requests
  if (req.method !== 'GET') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  // Get address from query parameters
  const { address } = req.query;

  if (!address) {
    return res.status(400).json({ error: 'Address parameter is required' });
  }

  try {
    // Use Mapbox Geocoding API
    const apiUrl = `https://api.mapbox.com/geocoding/v5/mapbox.places/${encodeURIComponent(address)}.json?access_token=${mapboxToken}`;
    
    const { data } = await axios.get(apiUrl);
    
    // Transform Mapbox response to match Google Maps format that the client expects
    let transformedResponse = {
      results: [],
      status: data.features.length > 0 ? 'OK' : 'ZERO_RESULTS'
    };
    
    if (data.features && data.features.length > 0) {
      const feature = data.features[0];
      transformedResponse.results = [{
        formatted_address: feature.place_name,
        geometry: {
          location: {
            lat: feature.center[1],
            lng: feature.center[0]
          }
        }
      }];
    }
    
    return res.status(200).json(transformedResponse);
  } catch (error) {
    console.error('Geocoding error:', error.message);
    
    // Create an error response that matches Google's format for consistency
    return res.status(500).json({
      results: [],
      status: 'ERROR',
      error_message: error.message
    });
  }
} 