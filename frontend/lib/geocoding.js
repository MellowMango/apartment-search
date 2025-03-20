/**
 * Geocoding utilities for the frontend
 * 
 * This module provides tools for:
 * 1. Client-side geocoding using Google Maps, Mapbox, or Nominatim (fallback)
 * 2. Utilities for coordinate validation and processing
 * 3. Functions to synchronize coordinates between properties and property_research
 */

import { supabase } from './supabase';

/**
 * Geocode a batch of properties
 * 
 * @param {Array} properties - Array of property objects
 * @returns {Promise<Array>} - Properties with coordinates added
 */
export async function geocodeProperties(properties) {
  // Filter properties that need geocoding
  const needsGeocoding = properties.filter(p => 
    (p._needs_geocoding || !p.latitude || !p.longitude || p._coordinates_missing || p._is_grid_pattern) &&
    (p.address || (p.city && p.state))
  );
  
  if (needsGeocoding.length === 0) {
    console.log('No properties need geocoding');
    return properties;
  }
  
  console.log(`Geocoding ${needsGeocoding.length} properties`);
  
  // Try to use Google Maps API if available
  const googleMapsAvailable = typeof google !== 'undefined' && 
                             google.maps && 
                             google.maps.Geocoder;
                             
  // Use Mapbox if available
  const mapboxToken = process.env.NEXT_PUBLIC_MAPBOX_ACCESS_TOKEN;
  
  // Geocode each property
  const geocodedProperties = await Promise.all(
    properties.map(async (property) => {
      // Skip properties that don't need geocoding
      if ((!property._needs_geocoding && property.latitude && property.longitude && 
           !property._coordinates_missing && !property._is_grid_pattern) ||
          (!property.address && (!property.city || !property.state))) {
        return property;
      }
      
      // Create a copy to avoid mutating the original
      const geocodedProperty = { ...property };
      
      try {
        let coordinates = null;
        
        // Try Google Maps API first if available
        if (googleMapsAvailable) {
          coordinates = await geocodeWithGoogleMaps(property);
        }
        
        // If Google Maps failed or is not available, try Mapbox
        if (!coordinates && mapboxToken) {
          coordinates = await geocodeWithMapbox(property, mapboxToken);
        }
        
        // If both failed, try Nominatim as a last resort
        if (!coordinates) {
          coordinates = await geocodeWithNominatim(property);
        }
        
        // If we got coordinates, update the property
        if (coordinates) {
          geocodedProperty.latitude = coordinates.latitude;
          geocodedProperty.longitude = coordinates.longitude;
          geocodedProperty._geocoded = true;
          geocodedProperty._coordinates_missing = false;
          geocodedProperty._needs_geocoding = false;
          geocodedProperty._is_grid_pattern = false;
          
          console.log(`Geocoded ${property.address || property.city}, ${property.state}: ${coordinates.latitude}, ${coordinates.longitude}`);
        } else {
          console.warn(`Failed to geocode ${property.address || property.city}, ${property.state}`);
        }
      } catch (error) {
        console.error(`Geocoding error for ${property.address || property.city}, ${property.state}:`, error);
      }
      
      return geocodedProperty;
    })
  );
  
  return geocodedProperties;
}

/**
 * Geocode a property using Google Maps API
 * 
 * @param {Object} property - Property object with address information
 * @returns {Promise<Object|null>} - Coordinates object or null if failed
 */
async function geocodeWithGoogleMaps(property) {
  return new Promise((resolve) => {
    try {
      const geocoder = new google.maps.Geocoder();
      
      // Build address string
      let addressString = '';
      if (property.address) addressString += property.address;
      if (property.city) addressString += (addressString ? ', ' : '') + property.city;
      if (property.state) addressString += (addressString ? ', ' : '') + property.state;
      if (property.zip_code) addressString += (addressString ? ' ' : '') + property.zip_code;
      
      geocoder.geocode({ address: addressString }, (results, status) => {
        if (status === 'OK' && results[0] && results[0].geometry) {
          const latitude = results[0].geometry.location.lat();
          const longitude = results[0].geometry.location.lng();
          
          // Check for suspicious patterns
          if (isGridPattern(latitude, longitude)) {
            console.warn(`Suspicious grid pattern detected: ${latitude}, ${longitude}`);
            resolve(null);
          } else {
            resolve({
              latitude,
              longitude,
              provider: 'google'
            });
          }
        } else {
          console.warn(`Google geocoding failed: ${status}`);
          resolve(null);
        }
      });
    } catch (error) {
      console.error('Error with Google geocoding:', error);
      resolve(null);
    }
  });
}

/**
 * Geocode a property using Mapbox API
 * 
 * @param {Object} property - Property object with address information
 * @param {string} accessToken - Mapbox access token
 * @returns {Promise<Object|null>} - Coordinates object or null if failed
 */
async function geocodeWithMapbox(property, accessToken) {
  try {
    // Build address string
    let addressString = '';
    if (property.address) addressString += property.address;
    if (property.city) addressString += (addressString ? ', ' : '') + property.city;
    if (property.state) addressString += (addressString ? ', ' : '') + property.state;
    if (property.zip_code) addressString += (addressString ? ' ' : '') + property.zip_code;
    
    // URL encode the address
    const encodedAddress = encodeURIComponent(addressString);
    
    // Make API request
    const response = await fetch(
      `https://api.mapbox.com/geocoding/v5/mapbox.places/${encodedAddress}.json?access_token=${accessToken}`
    );
    
    if (!response.ok) {
      throw new Error(`Mapbox API error: ${response.status} ${response.statusText}`);
    }
    
    const data = await response.json();
    
    if (data.features && data.features.length > 0) {
      const feature = data.features[0];
      const longitude = feature.center[0];
      const latitude = feature.center[1];
      
      // Check for suspicious patterns
      if (isGridPattern(latitude, longitude)) {
        console.warn(`Suspicious grid pattern detected: ${latitude}, ${longitude}`);
        return null;
      }
      
      return {
        latitude,
        longitude,
        provider: 'mapbox'
      };
    }
    
    return null;
  } catch (error) {
    console.error('Error with Mapbox geocoding:', error);
    return null;
  }
}

/**
 * Geocode a property using Nominatim API (OpenStreetMap)
 * 
 * @param {Object} property - Property object with address information
 * @returns {Promise<Object|null>} - Coordinates object or null if failed
 */
async function geocodeWithNominatim(property) {
  try {
    // Build address string
    let addressString = '';
    if (property.address) addressString += property.address;
    if (property.city) addressString += (addressString ? ', ' : '') + property.city;
    if (property.state) addressString += (addressString ? ', ' : '') + property.state;
    if (property.zip_code) addressString += (addressString ? ' ' : '') + property.zip_code;
    
    // URL encode the address
    const encodedAddress = encodeURIComponent(addressString);
    
    // Make API request (with a random delay to avoid rate limiting)
    const response = await fetch(
      `https://nominatim.openstreetmap.org/search?format=json&q=${encodedAddress}`,
      {
        headers: {
          'User-Agent': 'AcquirePropertyMap/1.0'
        }
      }
    );
    
    if (!response.ok) {
      throw new Error(`Nominatim API error: ${response.status} ${response.statusText}`);
    }
    
    const data = await response.json();
    
    if (data && data.length > 0) {
      const result = data[0];
      const latitude = parseFloat(result.lat);
      const longitude = parseFloat(result.lon);
      
      // Check for suspicious patterns
      if (isGridPattern(latitude, longitude)) {
        console.warn(`Suspicious grid pattern detected: ${latitude}, ${longitude}`);
        return null;
      }
      
      return {
        latitude,
        longitude,
        provider: 'nominatim'
      };
    }
    
    return null;
  } catch (error) {
    console.error('Error with Nominatim geocoding:', error);
    return null;
  }
}

/**
 * Check if coordinates are likely part of a grid pattern
 * 
 * @param {number} latitude - Latitude coordinate
 * @param {number} longitude - Longitude coordinate
 * @returns {boolean} - True if likely a grid pattern, false otherwise
 */
export function isGridPattern(latitude, longitude) {
  if (!latitude || !longitude) return false;
  
  // Convert to strings for easier checking
  const latStr = String(latitude);
  const lngStr = String(longitude);
  
  // Check for very low precision coordinates (often grid patterns)
  const hasLowPrecision = 
    (latStr.includes('.') && latStr.split('.')[1].length <= 3) ||
    (lngStr.includes('.') && lngStr.split('.')[1].length <= 3);
    
  // Check for suspicious patterns
  const hasSuspiciousPattern = 
    latStr === lngStr || // Same lat/lng is very unlikely
    latStr.endsWith('00000') || 
    lngStr.endsWith('00000') ||
    latStr.endsWith('.5') || // Common grid values
    lngStr.endsWith('.5') ||
    latStr.endsWith('.0') ||
    lngStr.endsWith('.0');
    
  return hasLowPrecision || hasSuspiciousPattern;
}

/**
 * Check if the property_research table exists in Supabase
 * 
 * @returns {Promise<boolean>} - True if table exists, false otherwise
 */
export async function checkResearchTableExists() {
  try {
    // Attempt to query the table
    const { error } = await supabase
      .from('property_research')
      .select('id')
      .limit(1);
    
    // If no error, table exists
    return !error;
  } catch (error) {
    console.error('Error checking research table:', error);
    return false;
  }
}

/**
 * Synchronize coordinates between properties and property_research tables
 * 
 * @param {number} limit - Maximum number of properties to process
 * @returns {Promise<Object>} - Result object with success status and counts
 */
export async function syncResearchCoordinates(limit = 100) {
  try {
    // Check if table exists
    const tableExists = await checkResearchTableExists();
    if (!tableExists) {
      return {
        success: false,
        message: 'Property research table does not exist or is not accessible',
        updated: 0,
        errors: 0
      };
    }
    
    // Get properties missing or with suspicious coordinates
    const { data: properties, error } = await supabase
      .from('properties')
      .select('id, address, city, state, zip_code, latitude, longitude')
      .limit(limit);
      
    if (error) {
      throw new Error(`Error fetching properties: ${error.message}`);
    }
    
    if (!properties || properties.length === 0) {
      return {
        success: true,
        message: 'No properties found to synchronize',
        updated: 0,
        errors: 0
      };
    }
    
    // Synchronize each property
    let updated = 0;
    let errors = 0;
    
    for (const property of properties) {
      try {
        // If property has valid coordinates, update property_research
        if (property.latitude && property.longitude && 
            !isGridPattern(property.latitude, property.longitude)) {
          
          // Get property_research record
          const { data: research, error: researchError } = await supabase
            .from('property_research')
            .select('id, modules')
            .eq('property_id', property.id);
            
          if (researchError) {
            console.error(`Error fetching research for property ${property.id}:`, researchError);
            errors++;
            continue;
          }
          
          if (research && research.length > 0) {
            // Update modules with coordinates
            const researchRecord = research[0];
            let modules = researchRecord.modules || {};
            
            // Create property_details if it doesn't exist
            if (!modules.property_details) {
              modules.property_details = {};
            }
            
            // Update coordinates
            modules.property_details.latitude = property.latitude;
            modules.property_details.longitude = property.longitude;
            modules.property_details.address = property.address;
            modules.property_details.city = property.city;
            modules.property_details.state = property.state;
            modules.property_details.zip_code = property.zip_code;
            
            // Update property_research
            const { error: updateError } = await supabase
              .from('property_research')
              .update({ modules })
              .eq('id', researchRecord.id);
              
            if (updateError) {
              console.error(`Error updating research for property ${property.id}:`, updateError);
              errors++;
            } else {
              updated++;
            }
          }
        }
      } catch (propertyError) {
        console.error(`Error processing property ${property.id}:`, propertyError);
        errors++;
      }
    }
    
    return {
      success: true,
      message: `Synchronized ${updated} properties with ${errors} errors`,
      updated,
      errors
    };
  } catch (error) {
    console.error('Error in syncResearchCoordinates:', error);
    return {
      success: false,
      message: error.message || 'Unknown error occurred',
      updated: 0,
      errors: 1
    };
  }
}