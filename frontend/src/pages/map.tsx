import React, { useState, useEffect, useCallback, useRef } from 'react';
import dynamic from 'next/dynamic';
import Layout from '../components/Layout';
import { useAuth } from '../contexts/AuthContext';
import { Button } from '../components/ui/button';
import { Card, CardContent } from '../components/ui/card';
import { Alert, AlertDescription } from '../components/ui/alert';
import { AlertCircle, FileText, MapPin, Filter, Settings, Map } from 'lucide-react';
import { Property } from '../types/property';
import { fetchMapProperties, geocodeProperties, cleanProperties, analyzeProperties } from '../utils/api';

// Import API_URL from api.ts
// This is a workaround to get access to the API URL for logging purposes
const API_URL = typeof window !== 'undefined' 
  ? (
      // For local development, use relative URL
      window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
        ? 'http://localhost:3001/api'
        // For production, use the configured API URL
        : (process.env.NEXT_PUBLIC_API_URL || '/api')
    )
  : '/api';

// Define types for map bounds and logs
interface MapBounds {
  north: number;
  south: number;
  east: number;
  west: number;
}

interface LogEntry {
  message: string;
  timestamp: string;
  type: 'success' | 'error' | 'warning' | 'info' | 'detail';
}

interface DataStats {
  totalProperties: number;
  invalidCoordinates: number;
  missingCoordinates: number;
  zeroCoordinates: number;
  invalidRange: number;
  duplicatedLocations: number;
  uniqueLocations?: number;
}

interface MapFilters {
  showAvailable: boolean;
  showUnderContract: boolean;
  showSold: boolean;
}

// Import the map component dynamically to avoid SSR issues with Leaflet
const MapComponent = dynamic(
  () => import('../components/MapComponent'),
  { ssr: false }
);

export default function MapPage() {
  const { isAdmin } = useAuth();
  const [properties, setProperties] = useState<Property[]>([]);
  const [selectedProperty, setSelectedProperty] = useState<Property | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [geocoding, setGeocoding] = useState<boolean>(false);
  const [geocodingLogs, setGeocodingLogs] = useState<LogEntry[]>([]);
  const [showGeocodingLogs, setShowGeocodingLogs] = useState<boolean>(false);
  const [cleaning, setCleaning] = useState<boolean>(false);
  const [cleaningLogs, setCleaningLogs] = useState<LogEntry[]>([]);
  const [showCleaningLogs, setShowCleaningLogs] = useState<boolean>(false);
  const [enriching, setEnriching] = useState<boolean>(false);
  const [enrichingLogs, setEnrichingLogs] = useState<LogEntry[]>([]);
  const [showEnrichingLogs, setShowEnrichingLogs] = useState<boolean>(false);
  const [mapBounds, setMapBounds] = useState<MapBounds | null>(null);
  const [totalFetched, setTotalFetched] = useState<number>(0);
  const [sidebarState, setSidebarState] = useState<'open' | 'collapsed' | 'fullscreen'>('open');
  const [dataStats, setDataStats] = useState<DataStats>({
    totalProperties: 0,
    invalidCoordinates: 0,
    missingCoordinates: 0,
    zeroCoordinates: 0,
    invalidRange: 0,
    duplicatedLocations: 0
  });
  const [lastBounds, setLastBounds] = useState<MapBounds | null>(null);
  const [sidebarWidth, setSidebarWidth] = useState<number>(400); // Default width in pixels
  const [isResizing, setIsResizing] = useState<boolean>(false);
  const sidebarRef = useRef<HTMLDivElement | null>(null);
  const resizerRef = useRef<HTMLDivElement | null>(null);
  const [mapFilters, setMapFilters] = useState<MapFilters>({
    showAvailable: true,
    showUnderContract: true,
    showSold: true
  });
  const [error, setError] = useState<string | null>(null);

  // Initial property load on page load
  useEffect(() => {
    loadProperties();
  }, []);

  // Reload properties when map bounds change
  useEffect(() => {
    if (mapBounds) {
      console.log('Map bounds changed, loading properties in the visible area');
      loadProperties(mapBounds);
    }
  }, [mapBounds]);

  // Handle map bounds changes
  const handleBoundsChange = useCallback((bounds: MapBounds) => {
    setMapBounds(bounds);
  }, []);

  // Calculate statistics about the property data
  const calculateStats = useCallback((propData: Property[]) => {
    if (!propData || !Array.isArray(propData)) return;
    
    const missingCoords = propData.filter(p => !p.latitude || !p.longitude).length;
    const zeroCoords = propData.filter(p => p.latitude === 0 && p.longitude === 0).length;
    const invalidRange = propData.filter(p => {
      if (!p.latitude || !p.longitude) return false;
      const lat = typeof p.latitude === 'number' ? p.latitude : parseFloat(String(p.latitude));
      const lng = typeof p.longitude === 'number' ? p.longitude : parseFloat(String(p.longitude));
      return (isNaN(lat) || isNaN(lng) || lat < -90 || lat > 90 || lng < -180 || lng > 180);
    }).length;
    
    // Count properties at identical coordinates
    const coordMap = new Map<string, number>();
    let duplicatedCoords = 0;
    
    propData.forEach(p => {
      if (p.latitude && p.longitude) {
        const coordKey = `${p.latitude},${p.longitude}`;
        if (coordMap.has(coordKey)) {
          coordMap.set(coordKey, coordMap.get(coordKey) + 1);
          duplicatedCoords++;
        } else {
          coordMap.set(coordKey, 1);
        }
      }
    });
    
    setDataStats({
      totalProperties: propData.length,
      invalidCoordinates: missingCoords + zeroCoords + invalidRange,
      missingCoordinates: missingCoords,
      zeroCoordinates: zeroCoords,
      invalidRange: invalidRange,
      duplicatedLocations: duplicatedCoords,
      uniqueLocations: coordMap.size
    });
  }, []);

  // Function to handle errors consistently
  function handleApiError(error: any) {
    const errorMessage = error?.message || 'Error loading properties';
    const errorCode = error?.code || 'unknown_error';
    
    console.error('API Error:', errorMessage, error);
    
    // Check if we need to show a specific message to the user
    if (errorCode === 'unauthorized') {
      setError('Please log in to view properties');
    } else if (errorCode === 'not_found') {
      setError('No properties found in this area');
    } else if (errorCode === 'rate_limit_exceeded') {
      setError('Too many requests. Please try again later.');
    } else {
      setError(`Error: ${errorMessage}`);
    }
  }

  // Function to load properties with optional bounds filter
  async function loadProperties(bounds: MapBounds | null = null) {
    try {
      setLoading(true);
      
      // Create options for the API call
      const options: any = {
        page: 1,
        pageSize: 100
      };
      
      // Apply bounds filter if provided
      if (bounds) {
        options.bounds = bounds;
        
        // Only load more properties if the bounds have changed significantly
        const boundsChanged = hasSignificantBoundsChange(bounds, lastBounds);
        if (!boundsChanged) {
          setLoading(false);
          return;
        }
        setLastBounds(bounds);
      }
      
      // Add map filters
      options.showAvailable = mapFilters.showAvailable;
      options.showUnderContract = mapFilters.showUnderContract;
      options.showSold = mapFilters.showSold;

      // Fetch properties using the API client
      const data = await fetchMapProperties(options);
      
      // Reset error if successful
      setError(null);
      
      // Calculate statistics
      calculateStats(data);
      
      // Enhanced logging for debugging
      console.log(`Loaded ${data.length} properties for map`);
      
      // Filter out properties with invalid coordinates
      const validProperties = data.filter(p => 
        p.latitude && 
        p.longitude && 
        typeof p.latitude === 'number' && 
        typeof p.longitude === 'number' &&
        !(p.latitude === 0 && p.longitude === 0) &&
        p.latitude >= 29.5 && p.latitude <= 31.0 && 
        p.longitude >= -98.0 && p.longitude <= -97.0
      );
      
      setProperties(validProperties);
      setTotalFetched(validProperties.length);
    } catch (error: any) {
      handleApiError(error);
    } finally {
      setLoading(false);
    }
  }

  // Helper function to check if map bounds have changed significantly
  function hasSignificantBoundsChange(newBounds: MapBounds, oldBounds: MapBounds | null) {
    if (!oldBounds) return true;
    
    const oldArea = (oldBounds.north - oldBounds.south) * (oldBounds.east - oldBounds.west);
    const newArea = (newBounds.north - newBounds.south) * (newBounds.east - newBounds.west);
    
    const oldCenterLat = (oldBounds.north + oldBounds.south) / 2;
    const oldCenterLng = (oldBounds.east + oldBounds.west) / 2;
    const newCenterLat = (newBounds.north + newBounds.south) / 2;
    const newCenterLng = (newBounds.east + newBounds.west) / 2;
    
    const centerShift = Math.sqrt(
      Math.pow(newCenterLat - oldCenterLat, 2) + 
      Math.pow(newCenterLng - oldCenterLng, 2)
    );
    
    const areaRatio = Math.max(newArea / oldArea, oldArea / newArea);
    return areaRatio > 1.5 || centerShift > 0.1;
  }

  // Function to handle sidebar state change
  const handleSidebarStateChange = (state: 'open' | 'collapsed' | 'fullscreen') => {
    setSidebarState(state);
  };

  // Function to batch geocode properties with missing coordinates
  async function batchGeocodeProperties() {
    try {
      setGeocoding(true);
      clearGeocodingLogs();
      setShowGeocodingLogs(true);
      
      // Filter properties that need geocoding
      const propsToGeocode = properties.filter(p => 
        !p.latitude || !p.longitude || 
        p.latitude === 0 || p.longitude === 0 ||
        p._coordinates_missing || p._needs_geocoding ||
        p._is_grid_pattern
      );
      
      if (propsToGeocode.length === 0) {
        addGeocodingLog('No properties need geocoding', 'info');
        alert('No properties need geocoding');
        setGeocoding(false);
        return;
      }
      
      // Confirm with user
      addGeocodingLog(`Found ${propsToGeocode.length} properties that need geocoding`, 'info');
      if (!confirm(`This will attempt to geocode ${propsToGeocode.length} properties with missing or invalid coordinates. Continue?`)) {
        addGeocodingLog('Geocoding cancelled by user', 'warning');
        setGeocoding(false);
        return;
      }
      
      addGeocodingLog(`Starting batch geocoding of ${propsToGeocode.length} properties`, 'info');
      
      // Process in batches of 25 to avoid rate limits
      const batchSize = 25;
      const batches = Math.ceil(propsToGeocode.length / batchSize);
      let successCount = 0;
      let failCount = 0;
      
      for (let i = 0; i < batches; i++) {
        const start = i * batchSize;
        const end = Math.min(start + batchSize, propsToGeocode.length);
        const batch = propsToGeocode.slice(start, end);
        
        addGeocodingLog(`Processing batch ${i+1}/${batches} (${batch.length} properties)`, 'info');
        console.log(`Processing batch ${i+1}/${batches} (${batch.length} properties)`);
        
        try {
          // For each property in the batch, log the property being processed
          batch.forEach((property, idx) => {
            const propertyName = property.name || `Property #${property.id}`;
            addGeocodingLog(`[${i+1}.${idx+1}] Queuing ${propertyName}`, 'detail');
          });
          
          // Call the API's geocode function with a callback for each property
          const geocodedBatch = await geocodeProperties(batch, (property, status, details) => {
            // This callback will be called for each property as it's processed
            const propertyName = property.name || `Property #${property.id}`;
            if (status === 'success') {
              addGeocodingLog(`Geocoded: ${propertyName} (${details})`, 'success');
              successCount++;
            } else if (status === 'error') {
              addGeocodingLog(`Failed: ${propertyName} (${details})`, 'error');
              failCount++;
            } else {
              addGeocodingLog(`${status}: ${propertyName} ${details ? `(${details})` : ''}`, 'info');
            }
          });
          
          addGeocodingLog(`Batch ${i+1}/${batches} complete - ${geocodedBatch.length} properties processed`, 'success');
          
          // Update the properties list with the geocoded properties
          setProperties(prevProps => {
            const updatedProps = [...prevProps];
            geocodedBatch.forEach(geocodedProp => {
              const index = updatedProps.findIndex(p => p.id === geocodedProp.id);
              if (index >= 0) {
                updatedProps[index] = geocodedProp;
              }
            });
            return updatedProps;
          });
          
        } catch (error: any) {
          addGeocodingLog(`Error processing batch ${i+1}/${batches}: ${error.message || 'Unknown error'}`, 'error');
          failCount += batch.length;
          console.error(`Error processing batch ${i+1}/${batches}:`, error);
        }
        
        // Small delay to avoid rate limits
        if (i < batches - 1) {
          addGeocodingLog('Waiting before processing next batch...', 'info');
          await new Promise(resolve => setTimeout(resolve, 1000));
        }
      }
      
      addGeocodingLog(`Geocoding complete. ${successCount} successful, ${failCount} failed.`, successCount > 0 ? 'success' : 'warning');
      
      // Reload properties to ensure we have the latest data
      await loadProperties(mapBounds);
      
    } catch (error: any) {
      console.error('Error in batch geocoding:', error);
      addGeocodingLog(`Error in batch geocoding: ${error.message || 'Unknown error'}`, 'error');
    } finally {
      setGeocoding(false);
    }
  }

  // Function to clean property data (format addresses, names, etc.)
  async function cleanPropertyData() {
    try {
      setCleaning(true);
      clearCleaningLogs();
      setShowCleaningLogs(true);
      
      addCleaningLog('Starting data cleaning process', 'info');
      
      if (properties.length === 0) {
        addCleaningLog('No properties to clean', 'warning');
        alert('No properties available to clean');
        setCleaning(false);
        return;
      }
      
      // Confirm with user
      if (!confirm(`This will attempt to clean the data for ${properties.length} properties. Continue?`)) {
        addCleaningLog('Data cleaning cancelled by user', 'warning');
        setCleaning(false);
        return;
      }
      
      // Process properties in batches
      const batchSize = 25;
      const propertiesArray = [...properties];
      const totalBatches = Math.ceil(propertiesArray.length / batchSize);
      
      addCleaningLog(`Processing ${propertiesArray.length} properties in ${totalBatches} batches`, 'info');
      
      let processed = 0;
      let cleaned = 0;
      
      for (let i = 0; i < totalBatches; i++) {
        const start = i * batchSize;
        const end = Math.min(start + batchSize, propertiesArray.length);
        const batch = propertiesArray.slice(start, end);
        const batchIds = batch.map(p => p.id);
        
        addCleaningLog(`Processing batch ${i+1}/${totalBatches} (${batch.length} properties)`, 'info');
        
        try {
          // Call the API to clean the properties
          const cleanedProperties = await cleanProperties(batchIds);
          
          // Update the properties in the UI
          if (cleanedProperties.length > 0) {
            setProperties(prevProps => {
              const updated = [...prevProps];
              cleanedProperties.forEach(cleanedProp => {
                const index = updated.findIndex(p => p.id === cleanedProp.id);
                if (index >= 0) {
                  updated[index] = cleanedProp;
                  addCleaningLog(`Cleaned: ${cleanedProp.name || `Property #${cleanedProp.id}`}`, 'success');
                }
              });
              return updated;
            });
            
            cleaned += cleanedProperties.length;
          }
          
          processed += batch.length;
          addCleaningLog(`Batch ${i+1}/${totalBatches} complete - ${cleanedProperties.length} properties cleaned`, 'success');
        } catch (error: any) {
          console.error(`Error cleaning batch ${i+1}:`, error);
          addCleaningLog(`Error with batch ${i+1}: ${error.message || 'Unknown error'}`, 'error');
        }
        
        // Delay between batches
        if (i < totalBatches - 1) {
          await new Promise(resolve => setTimeout(resolve, 500));
        }
      }
      
      addCleaningLog(`Data cleaning complete. ${cleaned} properties cleaned out of ${processed} processed.`, 'success');
      
    } catch (error: any) {
      console.error('Error in data cleaning:', error);
      addCleaningLog(`Error in data cleaning: ${error.message || 'Unknown error'}`, 'error');
    } finally {
      setCleaning(false);
    }
  }

  // Function to run property analysis
  async function runPropertyAnalysis() {
    try {
      setEnriching(true);
      clearEnrichingLogs();
      setShowEnrichingLogs(true);
      
      addEnrichingLog('Starting property analysis', 'info');
      
      if (properties.length === 0) {
        addEnrichingLog('No properties to analyze', 'warning');
        alert('No properties available to analyze');
        setEnriching(false);
        return;
      }
      
      // Confirm with user
      if (!confirm(`This will analyze ${properties.length} properties. Continue?`)) {
        addEnrichingLog('Analysis cancelled by user', 'warning');
        setEnriching(false);
        return;
      }
      
      // Get all property IDs
      const propertyIds = properties.map(p => p.id);
      
      addEnrichingLog(`Analyzing ${propertyIds.length} properties...`, 'info');
      
      // Call the API to analyze the properties
      const analysisResults = await analyzeProperties(propertyIds);
      
      // Display results
      if (analysisResults) {
        // Duplicate checks
        if (analysisResults.duplicates) {
          addEnrichingLog(`Found ${analysisResults.duplicates.length} potential duplicates`, 'info');
          analysisResults.duplicates.forEach((duplicate: any) => {
            const { properties: dupeProps, reason } = duplicate;
            const propertyNames = dupeProps.map((p: any) => p.name || `#${p.id}`).join(', ');
            addEnrichingLog(`Potential duplicates: ${propertyNames} (${reason})`, 'warning');
          });
        }
        
        // Data quality issues
        if (analysisResults.dataQuality) {
          const issues = analysisResults.dataQuality;
          addEnrichingLog(`Data quality analysis complete`, 'info');
          
          if (issues.missingCoordinates) {
            addEnrichingLog(`${issues.missingCoordinates} properties missing coordinates`, 'warning');
          }
          
          if (issues.missingAddresses) {
            addEnrichingLog(`${issues.missingAddresses} properties missing addresses`, 'warning');
          }
          
          if (issues.missingNames) {
            addEnrichingLog(`${issues.missingNames} properties missing names`, 'warning');
          }
        }
        
        // Hotspots
        if (analysisResults.hotspots) {
          addEnrichingLog(`Found ${analysisResults.hotspots.length} location hotspots`, 'info');
          analysisResults.hotspots.forEach((hotspot: any) => {
            const { properties: hotProps, center } = hotspot;
            addEnrichingLog(`Hotspot at [${center.lat.toFixed(5)}, ${center.lng.toFixed(5)}] with ${hotProps.length} properties`, 'success');
          });
        }
      }
      
      addEnrichingLog('Analysis complete', 'success');
      
    } catch (error: any) {
      console.error('Error in property analysis:', error);
      addEnrichingLog(`Error in property analysis: ${error.message || 'Unknown error'}`, 'error');
    } finally {
      setEnriching(false);
    }
  }

  // Function to enrich property data with zero values
  async function enrichPropertyData() {
    try {
      setLoading(true);
      setEnriching(true);
      clearEnrichingLogs();
      setShowEnrichingLogs(true);
      
      addEnrichingLog("Starting data enrichment process...", "info");
      
      // Identify properties with suspicious zero values
      addEnrichingLog("Analyzing properties for suspicious zero values...", "info");
      
      const suspiciousProperties = properties.filter(p => 
        (p.units === 0 || p.num_units === 0)
      );
      
      if (suspiciousProperties.length === 0) {
        addEnrichingLog('No properties with suspicious zero values found', "success");
        alert('No properties with suspicious zero values found');
        setLoading(false);
        setEnriching(false);
        return;
      }
      
      addEnrichingLog(`Found ${suspiciousProperties.length} properties with suspicious zero values:`, "info");
      addEnrichingLog(`- ${suspiciousProperties.filter(p => p.units === 0).length} properties with zero units`, "detail");
      addEnrichingLog(`- ${suspiciousProperties.filter(p => p.num_units === 0).length} properties with zero units`, "detail");
      
      // Confirm with user
      const confirmation = confirm(
        `Found ${suspiciousProperties.length} properties with suspicious zero values:\n\n` +
        `- ${suspiciousProperties.filter(p => p.units === 0).length} properties with zero units\n` +
        `- ${suspiciousProperties.filter(p => p.num_units === 0).length} properties with zero units\n\n` +
        `Would you like to attempt to enrich these properties?`
      );
      
      if (!confirmation) {
        addEnrichingLog('Enrichment cancelled by user', "warning");
        setLoading(false);
        setEnriching(false);
        return;
      }
      
      // Make a copy of the properties for enrichment
      const enrichedProperties = [...properties];
      let enrichedCount = 0;
      
      // Analyze collections of similar properties to derive estimates
      addEnrichingLog("Analyzing property data for statistical enrichment...", "info");
      
      // Group properties by city/state for better comparison
      const cityStateGroups = {};
      properties.forEach(p => {
        if (p.city && p.state && p.price && p.price > 0 && (p.units > 0 || p.num_units > 0)) {
          const key = `${p.city.toLowerCase()},${p.state.toLowerCase()}`;
          if (!cityStateGroups[key]) {
            cityStateGroups[key] = [];
          }
          cityStateGroups[key].push(p);
        }
      });
      
      // Calculate median values per city/state
      const medianValues = {};
      Object.keys(cityStateGroups).forEach(key => {
        const group = cityStateGroups[key];
        if (group.length >= 3) { // Only use groups with enough data points
          // Calculate median price per unit
          const pricesPerUnit = group.map(p => {
            const units = p.units || p.num_units || 0;
            return units > 0 ? p.price / units : 0;
          }).filter(v => v > 0).sort((a, b) => a - b);
          
          const medianPricePerUnit = pricesPerUnit[Math.floor(pricesPerUnit.length / 2)];
          
          // Calculate median year built
          const yearBuilt = group.map(p => p.year_built).filter(y => y && y > 1900).sort((a, b) => a - b);
          const medianYearBuilt = yearBuilt.length > 0 ? yearBuilt[Math.floor(yearBuilt.length / 2)] : null;
          
          medianValues[key] = {
            medianPricePerUnit,
            medianYearBuilt,
            sampleSize: group.length
          };
          
          addEnrichingLog(`Group ${key}: ${group.length} properties, $${Math.round(medianPricePerUnit).toLocaleString()}/unit`, "detail");
        }
      });
      
      addEnrichingLog(`Created ${Object.keys(medianValues).length} statistical groups for comparison`, "info");
      addEnrichingLog(`Starting to process ${suspiciousProperties.length} properties with zero values...`, "info");
      
      // Enrich properties with suspicious zero values
      suspiciousProperties.forEach(property => {
        const index = enrichedProperties.findIndex(p => p.id === property.id);
        if (index === -1) return;
        
        let isEnriched = false;
        let enrichmentNotes = [];
        
        // Find the best reference group for this property
        let referenceGroup = null;
        let referenceKey = null;
        
        if (property.city && property.state) {
          const key = `${property.city.toLowerCase()},${property.state.toLowerCase()}`;
          if (medianValues[key]) {
            referenceGroup = medianValues[key];
            referenceKey = key;
            addEnrichingLog(`Property #${property.id}: Found exact city/state match (${key})`, "detail");
          }
        }
        
        // If no direct city/state match, use the closest geographically or a general average
        if (!referenceGroup) {
          // Fall back to state-level data or general average
          if (property.state) {
            const stateGroups = Object.keys(medianValues).filter(key => 
              key.endsWith(`,${property.state.toLowerCase()}`)
            );
            
            if (stateGroups.length > 0) {
              // Use the largest sample from the state
              referenceKey = stateGroups.sort((a, b) => 
                medianValues[b].sampleSize - medianValues[a].sampleSize
              )[0];
              referenceGroup = medianValues[referenceKey];
              addEnrichingLog(`Property #${property.id}: Found state-level match (${referenceKey})`, "detail");
            }
          }
          
          // If still no match, use the overall average
          if (!referenceGroup) {
            const allPricesPerUnit = properties
              .filter(p => p.price && p.price > 0 && (p.units > 0 || p.num_units > 0))
              .map(p => p.price / (p.units || p.num_units))
              .sort((a, b) => a - b);
              
            if (allPricesPerUnit.length > 0) {
              referenceGroup = {
                medianPricePerUnit: allPricesPerUnit[Math.floor(allPricesPerUnit.length / 2)],
                medianYearBuilt: null,
                sampleSize: allPricesPerUnit.length
              };
              referenceKey = "all_properties";
              addEnrichingLog(`Property #${property.id}: Using global average (${allPricesPerUnit.length} properties)`, "detail");
            }
          }
        }
        
        // Calculate missing values
        if (referenceGroup) {
          // Fix zero units if price is available
          if ((property.units === 0 || !property.units) && 
              (property.num_units === 0 || !property.num_units) && 
              property.price > 0 && 
              referenceGroup.medianPricePerUnit > 0) {
                
            const estimatedUnits = Math.round(property.price / referenceGroup.medianPricePerUnit);
            enrichedProperties[index].units = estimatedUnits;
            enrichedProperties[index].num_units = estimatedUnits;
            addEnrichingLog(`Property #${property.id}: Estimated ${estimatedUnits} units based on $${property.price.toLocaleString()} price`, "success");
            isEnriched = true;
            enrichmentNotes.push(`Estimated ${estimatedUnits} units based on price and ${referenceKey} median`);
          }
          
          // Add missing year built if we have a reference
          if ((!property.year_built || property.year_built < 1900) && referenceGroup.medianYearBuilt) {
            enrichedProperties[index].year_built = referenceGroup.medianYearBuilt;
            addEnrichingLog(`Property #${property.id}: Estimated year built as ${referenceGroup.medianYearBuilt}`, "success");
            isEnriched = true;
            enrichmentNotes.push(`Estimated year built as ${referenceGroup.medianYearBuilt} based on ${referenceKey} median`);
          }
        }
        
        // Flag property as needing human review if we couldn't enrich it
        if (!isEnriched) {
          // Mark as needing manual review
          if (!enrichedProperties[index]._data_quality_issues) {
            enrichedProperties[index]._data_quality_issues = [];
          }
          enrichedProperties[index]._data_quality_issues.push('needs_manual_review');
          addEnrichingLog(`Property #${property.id}: Insufficient data for enrichment, marked for manual review`, "warning");
          isEnriched = true;
          enrichmentNotes.push('Marked for manual review - insufficient data to make estimates');
        }
        
        // Update property with enrichment information
        if (isEnriched) {
          enrichedProperties[index]._data_enriched = true;
          enrichedProperties[index]._enrichment_notes = enrichmentNotes.join(', ');
          enrichedCount++;
        }
      });
      
      addEnrichingLog(`Enrichment processing complete. Enriched ${enrichedCount} properties.`, "success");
      
      // Update state with enriched properties
      addEnrichingLog("Updating property data with enriched values...", "info");
      setProperties(enrichedProperties);
      calculateStats(enrichedProperties);
      
      // Alert user of results
      addEnrichingLog("Data enrichment complete!", "success");
      alert(
        `Data enrichment complete!\n\n` +
        `- ${enrichedCount} properties were enriched or marked for review\n` +
        `- ${suspiciousProperties.filter(p => p.units === 0).length} properties with zero units processed\n` +
        `- ${suspiciousProperties.filter(p => p.num_units === 0).length} properties with zero units processed\n\n` +
        `Next steps:\n` +
        `1. Review the enriched data for accuracy\n` +
        `2. Properties marked for manual review need human attention\n` +
        `3. Use "Properties Analysis" to verify data quality`
      );
    } catch (error) {
      console.error('Error enriching property data:', error);
      addEnrichingLog(`Error: ${error.message}`, "error");
      alert(`Error enriching data: ${error.message}`);
    } finally {
      setLoading(false);
      setEnriching(false);
    }
  }

  // Function to add a log entry with timestamp
  const addGeocodingLog = useCallback((message: string, type: 'success' | 'error' | 'warning' | 'info' | 'detail' = 'info') => {
    const timestamp = new Date().toLocaleTimeString();
    setGeocodingLogs(prevLogs => [
      { message, timestamp, type },
      ...prevLogs.slice(0, 99) // Keep only the last 100 logs
    ]);
  }, []);

  // Clear logs when starting new geocoding process
  const clearGeocodingLogs = useCallback(() => {
    setGeocodingLogs([]);
  }, []);
  
  // Function to add a cleaning log entry with timestamp
  const addCleaningLog = useCallback((message: string, type: 'success' | 'error' | 'warning' | 'info' | 'detail' = 'info') => {
    const timestamp = new Date().toLocaleTimeString();
    setCleaningLogs(prevLogs => [
      { message, timestamp, type },
      ...prevLogs.slice(0, 99) // Keep only the last 100 logs
    ]);
  }, []);

  // Clear logs when starting new cleaning process
  const clearCleaningLogs = useCallback(() => {
    setCleaningLogs([]);
  }, []);
  
  // Function to add an enrichment log entry with timestamp
  const addEnrichingLog = useCallback((message: string, type: 'success' | 'error' | 'warning' | 'info' | 'detail' = 'info') => {
    const timestamp = new Date().toLocaleTimeString();
    setEnrichingLogs(prevLogs => [
      { message, timestamp, type },
      ...prevLogs.slice(0, 99) // Keep only the last 100 logs
    ]);
  }, []);

  // Clear logs when starting new enrichment process
  const clearEnrichingLogs = useCallback(() => {
    setEnrichingLogs([]);
  }, []);

  // Handle mouse down on resizer
  const handleMouseDown = (e: React.MouseEvent<HTMLDivElement>) => {
    setIsResizing(true);
    document.addEventListener('mousemove', handleMouseMove);
    document.addEventListener('mouseup', handleMouseUp);
  };

  // Handle mouse move while resizing
  const handleMouseMove = useCallback((e: MouseEvent) => {
    if (!isResizing) return;
    
    const newWidth = e.clientX;
    const minWidth = 300; // Minimum sidebar width
    const maxWidth = window.innerWidth * 0.6; // Maximum sidebar width (60% of window)
    
    if (newWidth >= minWidth && newWidth <= maxWidth) {
      setSidebarWidth(newWidth);
    }
  }, [isResizing]);

  // Handle mouse up after resizing
  const handleMouseUp = useCallback(() => {
    setIsResizing(false);
    document.removeEventListener('mousemove', handleMouseMove);
    document.removeEventListener('mouseup', handleMouseUp);
  }, [handleMouseMove]);

  // Clean up event listeners
  useEffect(() => {
    return () => {
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
    };
  }, [handleMouseMove, handleMouseUp]);

  // Function to get status display name and color class
  function getStatusDisplay(status?: string) {
    if (!status) return { text: 'Unknown', className: 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-200' };

    const statusLower = status.toLowerCase();
    
    if (statusLower.includes('available') || statusLower.includes('active')) {
      return { 
        text: 'Available', 
        className: 'px-2 py-0.5 rounded-full text-xs bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200' 
      };
    } 
    
    if (statusLower.includes('contract')) {
      return { 
        text: 'Under Contract', 
        className: 'px-2 py-0.5 rounded-full text-xs bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200' 
      };
    }
    
    if (statusLower.includes('sold')) {
      return { 
        text: 'Sold', 
        className: 'px-2 py-0.5 rounded-full text-xs bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200' 
      };
    }
    
    return { 
      text: status, 
      className: 'px-2 py-0.5 rounded-full text-xs bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-200' 
    };
  }

  return (
    <Layout title="Property Map | Acquire Apartments">
      <div className="relative bg-gray-50 dark:bg-gray-900 min-h-screen">
        {/* Top Navigation Bar */}
        <div className="bg-white dark:bg-gray-800 shadow-sm border-b border-gray-200 dark:border-gray-700">
          <div className="container mx-auto px-4 py-3">
            <div className="flex items-center justify-between">
              <div>
                <h1 className="text-xl font-bold text-gray-900 dark:text-white">Austin Multifamily Map</h1>
                <p className="text-sm text-gray-500 dark:text-gray-400">
                  {loading ? 'Loading properties...' : `${totalFetched} properties available`}
                </p>
              </div>
              
              {/* Admin Action Buttons - Only visible to admin users */}
              {isAdmin && (
                <div className="flex items-center space-x-3">
                  <Button
                    onClick={runPropertyAnalysis}
                    variant="outline"
                    size="sm"
                    className="flex items-center gap-2"
                  >
                    <FileText className="h-4 w-4" />
                    Analysis
                  </Button>
                  
                  <Button
                    onClick={batchGeocodeProperties}
                    disabled={geocoding}
                    variant="outline"
                    size="sm"
                    className={`flex items-center gap-2 ${
                      geocoding ? 'opacity-70 cursor-not-allowed' : ''
                    }`}
                  >
                    <MapPin className="h-4 w-4" />
                    {geocoding ? 'Geocoding...' : 'Geocode Missing'}
                  </Button>
                  
                  <Button
                    onClick={cleanPropertyData}
                    disabled={cleaning}
                    variant="outline"
                    size="sm"
                    className={`flex items-center gap-2 ${
                      cleaning ? 'opacity-70 cursor-not-allowed' : ''
                    }`}
                  >
                    <Settings className="h-4 w-4" />
                    {cleaning ? 'Cleaning...' : 'Clean Data'}
                  </Button>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Main Content Area */}
        <div className="flex h-[calc(100vh-4rem-57px)] overflow-hidden relative">
          {/* Property Sidebar */}
          <div
            ref={sidebarRef}
            style={{ 
              width: sidebarState === 'collapsed' ? '3rem' : 
                     sidebarState === 'fullscreen' ? '100%' : 
                     `${sidebarWidth}px`,
              minWidth: sidebarState === 'collapsed' ? '3rem' : '300px',
              maxWidth: sidebarState === 'fullscreen' ? '100%' : '60%'
            }}
            className={`flex-shrink-0 bg-white dark:bg-gray-800 border-r border-gray-200 dark:border-gray-700 transition-all duration-300 flex flex-col ${
              isResizing ? 'select-none' : ''
            }`}
          >
            {/* Sidebar Header with Filters */}
            <div className="p-4 border-b border-gray-200 dark:border-gray-700 space-y-4">
              {/* Search */}
              <div className="relative">
                <input
                  type="text"
                  placeholder="Search properties..."
                  className="w-full px-3 py-2 bg-gray-50 dark:bg-gray-700 rounded-lg text-sm border border-gray-200 dark:border-gray-600"
                  onChange={(e) => {
                    // Add search functionality here
                  }}
                />
              </div>

              {/* Status Filters */}
              <div className="flex flex-wrap gap-2">
                <button
                  onClick={() => setMapFilters(prev => ({ ...prev, showAvailable: !prev.showAvailable }))}
                  className={`px-3 py-1 rounded-full text-xs font-medium ${
                    mapFilters.showAvailable
                      ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200'
                      : 'bg-gray-100 text-gray-600 dark:bg-gray-700 dark:text-gray-300'
                  }`}
                >
                  Available
                </button>
                <button
                  onClick={() => setMapFilters(prev => ({ ...prev, showUnderContract: !prev.showUnderContract }))}
                  className={`px-3 py-1 rounded-full text-xs font-medium ${
                    mapFilters.showUnderContract
                      ? 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200'
                      : 'bg-gray-100 text-gray-600 dark:bg-gray-700 dark:text-gray-300'
                  }`}
                >
                  Under Contract
                </button>
                <button
                  onClick={() => setMapFilters(prev => ({ ...prev, showSold: !prev.showSold }))}
                  className={`px-3 py-1 rounded-full text-xs font-medium ${
                    mapFilters.showSold
                      ? 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200'
                      : 'bg-gray-100 text-gray-600 dark:bg-gray-700 dark:text-gray-300'
                  }`}
                >
                  Sold
                </button>
              </div>

              {/* Sort Options */}
              <select
                className="w-full px-3 py-2 bg-gray-50 dark:bg-gray-700 rounded-lg text-sm border border-gray-200 dark:border-gray-600"
                onChange={(e) => {
                  // Add sort functionality here
                }}
              >
                <option value="recent">Most Recent</option>
                <option value="units-high">Units (High to Low)</option>
                <option value="units-low">Units (Low to High)</option>
                <option value="year-new">Year Built (Newest)</option>
                <option value="year-old">Year Built (Oldest)</option>
              </select>
            </div>

            {/* Scrollable Properties List */}
            <div className="flex-1 overflow-y-auto">
              <div className="divide-y divide-gray-200 dark:divide-gray-700">
                {properties.map((property) => (
                  <div
                    key={property.id}
                    onClick={() => setSelectedProperty(property)}
                    className={`p-4 hover:bg-gray-50 dark:hover:bg-gray-700 cursor-pointer ${
                      selectedProperty?.id === property.id ? 'bg-blue-50 dark:bg-blue-900' : ''
                    }`}
                  >
                    <div className="flex items-start gap-3">
                      <div className="flex-shrink-0 w-16 h-16 bg-gray-100 dark:bg-gray-600 rounded overflow-hidden">
                        {property.image_url ? (
                          <img
                            src={property.image_url}
                            alt={property.name}
                            className="w-full h-full object-cover"
                          />
                        ) : (
                          <div className="w-full h-full flex items-center justify-center">
                            <svg xmlns="http://www.w3.org/2000/svg" className="h-8 w-8 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
                            </svg>
                          </div>
                        )}
                      </div>
                      <div className="flex-1 min-w-0">
                        <h3 className="text-sm font-medium truncate">{property.name}</h3>
                        <p className="text-xs text-gray-500 dark:text-gray-400 mt-1 truncate">
                          {property.address}
                        </p>
                        <div className="mt-2 flex items-center gap-2">
                          <span className={getStatusDisplay(property.status).className}>
                            {getStatusDisplay(property.status).text}
                          </span>
                          {(property.num_units || property.units) && (
                            <span className="text-xs text-gray-500 dark:text-gray-400">
                              {property.num_units || property.units} units
                            </span>
                          )}
                          {property.year_built && (
                            <span className="text-xs text-gray-500 dark:text-gray-400">
                              Built {property.year_built}
                            </span>
                          )}
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Resizer Handle */}
          {sidebarState !== 'collapsed' && sidebarState !== 'fullscreen' && (
            <div
              ref={resizerRef}
              onMouseDown={handleMouseDown}
              className={`absolute w-1 h-full cursor-col-resize group hover:bg-primary/10 active:bg-primary/20 ${
                isResizing ? 'bg-primary/20' : 'bg-transparent'
              }`}
              style={{ 
                left: `${sidebarWidth}px`,
                transform: 'translateX(-50%)'
              }}
            >
              <div className="absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 w-4 h-24 rounded-full flex items-center justify-center group-hover:bg-primary/5">
                <div className="w-0.5 h-12 bg-gray-300 dark:bg-gray-600 rounded-full group-hover:bg-primary/20 group-active:bg-primary/40" />
              </div>
            </div>
          )}
          
          {/* Map Container */}
          <div className={`flex-grow transition-all duration-300 ${
            sidebarState === 'fullscreen' ? 'hidden' : 'block'
          }`}>
            <div className="h-full relative">
              <MapComponent
                properties={properties}
                selectedProperty={selectedProperty}
                setSelectedProperty={setSelectedProperty}
                onBoundsChange={handleBoundsChange}
              />
              
              {/* Error message */}
              {error && (
                <div className="absolute top-4 left-1/2 transform -translate-x-1/2 z-50">
                  <Alert variant="destructive" className="w-auto max-w-md">
                    <AlertCircle className="h-4 w-4 mr-2" />
                    <AlertDescription>
                      {error}
                    </AlertDescription>
                  </Alert>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Status Logs */}
        <div className="fixed bottom-4 right-4 flex flex-col space-y-2 z-50">
          {/* Geocoding Logs */}
          {showGeocodingLogs && geocodingLogs.length > 0 && (
            <div className="w-96 max-h-64 bg-white dark:bg-gray-800 rounded-lg shadow-lg overflow-auto">
              <div className="sticky top-0 bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 p-2 flex justify-between items-center">
                <div className="flex items-center">
                  <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 text-blue-500 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                  </svg>
                  <h3 className="font-medium text-sm">Geocoding Progress</h3>
                </div>
                <button onClick={() => setShowGeocodingLogs(false)} className="text-gray-400 hover:text-gray-600">
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>
              <div className="p-2 space-y-1">
                {geocodingLogs.map((log, index) => (
                  <div key={index} className={`text-sm p-1 rounded ${
                    log.type === 'error' ? 'text-red-600 bg-red-50' :
                    log.type === 'warning' ? 'text-amber-600 bg-amber-50' :
                    log.type === 'success' ? 'text-green-600 bg-green-50' :
                    'text-gray-600 bg-gray-50'
                  }`}>
                    <span className="text-xs text-gray-400 mr-2">{log.timestamp}</span>
                    {log.message}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Cleaning Logs */}
          {showCleaningLogs && cleaningLogs.length > 0 && (
            <div className="w-96 max-h-64 bg-white dark:bg-gray-800 rounded-lg shadow-lg overflow-auto">
              <div className="sticky top-0 bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 p-2 flex justify-between items-center">
                <div className="flex items-center">
                  <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 text-green-500 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                  <h3 className="font-medium text-sm">Data Cleaning Progress</h3>
                </div>
                <button onClick={() => setShowCleaningLogs(false)} className="text-gray-400 hover:text-gray-600">
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>
              <div className="p-2 space-y-1">
                {cleaningLogs.map((log, index) => (
                  <div key={index} className={`text-sm p-1 rounded ${
                    log.type === 'error' ? 'text-red-600 bg-red-50' :
                    log.type === 'warning' ? 'text-amber-600 bg-amber-50' :
                    log.type === 'success' ? 'text-green-600 bg-green-50' :
                    'text-gray-600 bg-gray-50'
                  }`}>
                    <span className="text-xs text-gray-400 mr-2">{log.timestamp}</span>
                    {log.message}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </Layout>
  );
} 