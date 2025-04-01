/**
 * Geocoding utilities for the frontend
 * 
 * This module provides tools for:
 * 1. Client-side geocoding using Google Maps, Mapbox, or Nominatim (fallback)
 * 2. Utilities for coordinate validation and processing
 * 3. Functions to synchronize coordinates between properties and property_research
 */

import { supabase } from './supabase';
import { Property } from '../types/property';

declare global {
  interface Window {
    google?: {
      maps?: {
        Geocoder?: any;
      }
    }
  }
}

interface Coordinates {
  latitude: number;
  longitude: number;
  provider?: string;
}

/**
 * Geocode a batch of properties
 * 
 * @param {Array} properties - Array of property objects
 * @returns {Promise<Array>} - Properties with coordinates added
 */
export async function geocodeProperties(properties: Property[]): Promise<Property[]> {
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
  const googleMapsAvailable = typeof window !== 'undefined' && 
                             window.google && 
                             window.google.maps && 
                             window.google.maps.Geocoder;
                             
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
async function geocodeWithGoogleMaps(property: Property): Promise<Coordinates | null> {
  return new Promise((resolve) => {
    try {
      if (!window.google || !window.google.maps || !window.google.maps.Geocoder) {
        resolve(null);
        return;
      }
      
      const geocoder = new window.google.maps.Geocoder();
      
      // Build address string
      let addressString = '';
      if (property.address) addressString += property.address;
      if (property.city) addressString += (addressString ? ', ' : '') + property.city;
      if (property.state) addressString += (addressString ? ', ' : '') + property.state;
      if (property.zip) addressString += (addressString ? ' ' : '') + property.zip;
      
      geocoder.geocode({ address: addressString }, (results: any, status: string) => {
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
async function geocodeWithMapbox(property: Property, accessToken: string): Promise<Coordinates | null> {
  try {
    // Build address string
    let addressString = '';
    if (property.address) addressString += property.address;
    if (property.city) addressString += (addressString ? ', ' : '') + property.city;
    if (property.state) addressString += (addressString ? ', ' : '') + property.state;
    if (property.zip) addressString += (addressString ? ' ' : '') + property.zip;
    
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
async function geocodeWithNominatim(property: Property): Promise<Coordinates | null> {
  try {
    // Build address string
    let addressString = '';
    if (property.address) addressString += property.address;
    if (property.city) addressString += (addressString ? ', ' : '') + property.city;
    if (property.state) addressString += (addressString ? ', ' : '') + property.state;
    if (property.zip) addressString += (addressString ? ' ' : '') + property.zip;
    
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
 * Check if coordinates are on a grid pattern (indicating synthetic data)
 * 
 * @param {number} latitude - Latitude coordinate
 * @param {number} longitude - Longitude coordinate
 * @returns {boolean} - True if coordinates are likely on a grid
 */
export function isGridPattern(latitude: number, longitude: number): boolean {
  // Check if values are zero (common for uninitialized values)
  if (latitude === 0 && longitude === 0) {
    return true;
  }
  
  // Check if values have very few decimal places (likely rounded)
  const latStr = latitude.toString();
  const lngStr = longitude.toString();
  
  const latDecimals = latStr.includes('.') ? latStr.split('.')[1].length : 0;
  const lngDecimals = lngStr.includes('.') ? lngStr.split('.')[1].length : 0;
  
  // If both have fewer than 4 decimal places, it's likely synthetic
  if (latDecimals < 4 && lngDecimals < 4) {
    return true;
  }
  
  // Check if outside Austin area bounds (approximately)
  if (latitude < 29.5 || latitude > 31.0 || longitude < -98.0 || longitude > -97.0) {
    return true;
  }
  
  return false;
}

/**
 * Check if the property_research table exists
 * 
 * @returns {Promise<boolean>} - True if table exists
 */
export async function checkResearchTableExists(): Promise<boolean> {
  try {
    const { data, error } = await supabase
      .from('property_research')
      .select('id')
      .limit(1);
      
    if (error) {
      console.error('Error checking research table:', error);
      return false;
    }
    
    return true;
  } catch (error) {
    console.error('Error checking research table:', error);
    return false;
  }
}

/**
 * Synchronize coordinates between properties and property_research tables
 * 
 * @param {number} limit - Maximum number of records to process
 * @returns {Promise<Object>} - Results of the operation
 */
export async function syncResearchCoordinates(limit = 100): Promise<{
  total: number,
  updated: number,
  errors: number
}> {
  const results = {
    total: 0,
    updated: 0,
    errors: 0
  };
  
  try {
    // Check if research table exists
    const tableExists = await checkResearchTableExists();
    if (!tableExists) {
      console.error('Property research table does not exist');
      return results;
    }
    
    // Get properties with missing coordinates but have research data
    const { data, error } = await supabase
      .from('properties')
      .select(`
        id, 
        address, 
        city, 
        state, 
        latitude, 
        longitude,
        property_research!property_research (
          id, 
          modules
        )
      `)
      .or('latitude.is.null,longitude.is.null,latitude.eq.0,longitude.eq.0')
      .not('property_research', 'is', null)
      .limit(limit);
      
    if (error) {
      console.error('Error fetching properties with missing coordinates:', error);
      return results;
    }
    
    results.total = data.length;
    console.log(`Found ${data.length} properties with missing coordinates that have research data`);
    
    // Process each property
    for (const property of data) {
      try {
        // Extract research data if available
        const researchData = property.property_research && property.property_research.length > 0 
          ? property.property_research[0] 
          : null;
          
        if (researchData && researchData.modules && researchData.modules.property_details) {
          const propertyDetails = researchData.modules.property_details;
          
          // Check if research data has valid coordinates
          if (propertyDetails.latitude && propertyDetails.longitude &&
              typeof propertyDetails.latitude === 'number' && 
              typeof propertyDetails.longitude === 'number') {
              
            // Update property with coordinates from research data
            const { error: updateError } = await supabase
              .from('properties')
              .update({
                latitude: propertyDetails.latitude,
                longitude: propertyDetails.longitude,
                _coordinates_from_research: true,
                _coordinates_missing: false,
                _needs_geocoding: false
              })
              .match({ id: property.id });
              
            if (updateError) {
              console.error(`Error updating property ${property.id}:`, updateError);
              results.errors++;
            } else {
              console.log(`Updated property ${property.id} with coordinates from research: [${propertyDetails.latitude}, ${propertyDetails.longitude}]`);
              results.updated++;
            }
          }
        }
      } catch (e) {
        console.error(`Error processing property ${property.id}:`, e);
        results.errors++;
      }
    }
    
    return results;
  } catch (error) {
    console.error('Error syncing research coordinates:', error);
    return results;
  }
}

/**
 * Perform enhanced geocoding on a batch of properties
 * 
 * @param {Array} properties - Array of property objects
 * @param {Function} progressCallback - Optional callback for progress updates
 * @returns {Promise<Array>} - Properties with coordinates added
 */
export async function enhancedGeocodeProperties(
  properties: Property[], 
  progressCallback: ((progress: number, total: number) => void) | null = null
): Promise<Property[]> {
  if (!properties || properties.length === 0) {
    return [];
  }
  
  console.log(`Geocoding ${properties.length} properties using enhanced approach`);
  
  // Only process properties that need geocoding
  const needsGeocoding = properties.filter(p => 
    (p._needs_geocoding || !p.latitude || !p.longitude || p._coordinates_missing || p._is_grid_pattern) &&
    (p.address || (p.city && p.state))
  );
  
  // Keep properties that don't need geocoding
  const goodProperties = properties.filter(p => 
    !p._needs_geocoding && p.latitude && p.longitude && 
    !p._coordinates_missing && !p._is_grid_pattern &&
    hasValidCoordinates(p)
  );
  
  if (needsGeocoding.length === 0) {
    console.log('No properties need geocoding');
    return properties;
  }
  
  console.log(`Found ${needsGeocoding.length} properties that need geocoding`);
  
  // Function to report progress
  const reportProgress = (current: number, total: number) => {
    if (progressCallback) {
      progressCallback(current, total);
    }
  };
  
  // First, try to use Google Maps API (but respect rate limits)
  if (typeof window !== 'undefined' && window.google && window.google.maps && window.google.maps.Geocoder) {
    let processed = 0;
    let geocodedCount = 0;
    const geocoder = new window.google.maps.Geocoder();
    const batch = needsGeocoding.slice(0, 50); // Process up to 50 to respect quotas
    
    console.log(`Using Google Maps API to geocode ${batch.length} properties`);
    
    const geocodeBatch = async () => {
      const results: Property[] = [];
      
      for (const property of batch) {
        // Build address string
        let addressString = '';
        if (property.address) addressString += property.address;
        if (property.city) addressString += (addressString ? ', ' : '') + property.city;
        if (property.state) addressString += (addressString ? ', ' : '') + property.state;
        if (property.zip) addressString += (addressString ? ' ' : '') + property.zip;
        
        // Add a delay to avoid quota limits
        await new Promise(resolve => setTimeout(resolve, 250));
        
        try {
          const geocodePromise = new Promise<Coordinates | null>((resolve) => {
            geocoder.geocode({ address: addressString }, (results: any, status: string) => {
              if (status === 'OK' && results[0] && results[0].geometry) {
                const latitude = results[0].geometry.location.lat();
                const longitude = results[0].geometry.location.lng();
                
                if (isGridPattern(latitude, longitude)) {
                  resolve(null);
                } else {
                  resolve({
                    latitude,
                    longitude,
                    provider: 'google'
                  });
                }
              } else {
                resolve(null);
              }
            });
          });
          
          // Set a timeout to avoid hanging
          const timeoutPromise = new Promise<null>((resolve) => {
            setTimeout(() => resolve(null), 5000);
          });
          
          // Race the geocode promise against the timeout
          const coordinates = await Promise.race([geocodePromise, timeoutPromise]);
          
          if (coordinates) {
            const geocodedProperty = { ...property };
            geocodedProperty.latitude = coordinates.latitude;
            geocodedProperty.longitude = coordinates.longitude;
            geocodedProperty._geocoded = true;
            geocodedProperty._geocoding_source = 'full_address';
            geocodedProperty._geocoding_failed = false;
            geocodedProperty._coordinates_missing = false;
            geocodedProperty._needs_geocoding = false;
            geocodedProperty._is_grid_pattern = false;
            
            results.push(geocodedProperty);
            geocodedCount++;
          } else {
            results.push(property);
          }
        } catch (error) {
          console.error(`Error geocoding property:`, error);
          results.push(property);
        }
        
        processed++;
        reportProgress(processed, batch.length);
      }
      
      return results;
    };
    
    // Execute the batch geocoding
    const geocodedProperties = await geocodeBatch();
    console.log(`Successfully geocoded ${geocodedCount} out of ${batch.length} properties`);
    
    // Combine the geocoded properties with good properties
    return [...goodProperties, ...geocodedProperties];
  } else {
    // Fall back to the standard geocoding method
    console.log('Google Maps API not available, using fallback geocoding method');
    const geocodedProperties = await geocodeProperties(needsGeocoding);
    
    // Combine the geocoded properties with good properties
    return [...goodProperties, ...geocodedProperties];
  }
}

/**
 * Check if a property has valid coordinates
 * 
 * @param {Object} property - Property object
 * @returns {boolean} - True if coordinates are valid
 */
const hasValidCoordinates = (property: Property): boolean => {
  // Must have numeric coordinates
  if (!property.latitude || !property.longitude || 
      typeof property.latitude !== 'number' || 
      typeof property.longitude !== 'number') {
    return false;
  }
  
  // Coordinates must be within valid ranges
  if (property.latitude < -90 || property.latitude > 90 || 
      property.longitude < -180 || property.longitude > 180) {
    return false;
  }
  
  // Coordinates must not be (0,0)
  if (property.latitude === 0 && property.longitude === 0) {
    return false;
  }
  
  // For Austin area, coordinates should be in approximate region
  if (property.latitude < 29.5 || property.latitude > 31.0 || 
      property.longitude < -98.0 || property.longitude > -97.0) {
    // Mark as outside Austin but don't consider invalid
    //property._outside_austin = true;
    return false;
  }
  
  return true;
};

/**
 * Geocode a single address
 * 
 * @param {string} address - Address to geocode
 * @returns {Promise<Object|null>} - Coordinates object or null if failed
 */
export async function geocodeAddress(address: string): Promise<Coordinates | null> {
  if (!address) return null;
  
  // Try Google Maps API first if available
  if (typeof window !== 'undefined' && window.google && window.google.maps && window.google.maps.Geocoder) {
    try {
      const geocoder = new window.google.maps.Geocoder();
      
      return new Promise((resolve) => {
        geocoder.geocode({ address }, (results: any, status: string) => {
          if (status === 'OK' && results[0] && results[0].geometry) {
            const latitude = results[0].geometry.location.lat();
            const longitude = results[0].geometry.location.lng();
            
            resolve({
              latitude,
              longitude,
              provider: 'google'
            });
          } else {
            resolve(null);
          }
        });
      });
    } catch (error) {
      console.error('Error with Google geocoding:', error);
    }
  }
  
  // Try Mapbox if available
  const mapboxToken = process.env.NEXT_PUBLIC_MAPBOX_ACCESS_TOKEN;
  if (mapboxToken) {
    try {
      const encodedAddress = encodeURIComponent(address);
      
      const response = await fetch(
        `https://api.mapbox.com/geocoding/v5/mapbox.places/${encodedAddress}.json?access_token=${mapboxToken}`
      );
      
      if (!response.ok) {
        throw new Error(`Mapbox API error: ${response.status} ${response.statusText}`);
      }
      
      const data = await response.json();
      
      if (data.features && data.features.length > 0) {
        const feature = data.features[0];
        const longitude = feature.center[0];
        const latitude = feature.center[1];
        
        return {
          latitude,
          longitude,
          provider: 'mapbox'
        };
      }
    } catch (error) {
      console.error('Error with Mapbox geocoding:', error);
    }
  }
  
  // Try Nominatim as a last resort
  try {
    const encodedAddress = encodeURIComponent(address);
    
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
      
      return {
        latitude,
        longitude,
        provider: 'nominatim'
      };
    }
  } catch (error) {
    console.error('Error with Nominatim geocoding:', error);
  }
  
  return null;
} 