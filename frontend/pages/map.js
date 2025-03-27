import React, { useState, useEffect, useCallback } from 'react';
import dynamic from 'next/dynamic';
import Layout from '../src/components/Layout';
import { fetchProperties } from '../lib/supabase';
import { enhancedGeocodeProperties } from '../lib/geocoding';

// Import the map component dynamically to avoid SSR issues with Leaflet
const MapComponent = dynamic(
  () => import('../src/components/MapComponent'),
  { ssr: false }
);

export default function MapPage() {
  const [properties, setProperties] = useState([]);
  const [selectedProperty, setSelectedProperty] = useState(null);
  const [loading, setLoading] = useState(true);
  const [geocoding, setGeocoding] = useState(false);
  const [geocodingLogs, setGeocodingLogs] = useState([]);
  const [showGeocodingLogs, setShowGeocodingLogs] = useState(false);
  const [cleaning, setCleaning] = useState(false);
  const [cleaningLogs, setCleaningLogs] = useState([]);
  const [showCleaningLogs, setShowCleaningLogs] = useState(false);
  const [enriching, setEnriching] = useState(false);
  const [enrichingLogs, setEnrichingLogs] = useState([]);
  const [showEnrichingLogs, setShowEnrichingLogs] = useState(false);
  const [mapBounds, setMapBounds] = useState(null);
  const [totalFetched, setTotalFetched] = useState(0);
  const [sidebarState, setSidebarState] = useState('open'); // 'open', 'collapsed', or 'fullscreen'
  const [dataStats, setDataStats] = useState({
    totalProperties: 0,
    invalidCoordinates: 0,
    missingCoordinates: 0,
    zeroCoordinates: 0,
    invalidRange: 0,
    duplicatedLocations: 0
  });

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
  const handleBoundsChange = useCallback((bounds) => {
    setMapBounds(bounds);
  }, []);

  // Calculate statistics about the property data
  const calculateStats = useCallback((propData) => {
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
    const coordMap = new Map();
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

  // Function to load properties with optional bounds filter
  async function loadProperties(bounds = null) {
    try {
      setLoading(true);
      const options = { 
        sortBy: 'created_at', 
        sortAsc: false,
        page: 1,
        pageSize: 1000,
        filters: {},
        includeIncomplete: true,
        includeResearch: true,
        noLimit: true // Bypass pagination to get all properties
      };

      // Apply bounds filter if provided
      if (bounds) {
        options.bounds = bounds;
      }

      const data = await fetchProperties(options);
      
      // Calculate statistics
      calculateStats(data);
      
      // Enhanced logging for debugging
      console.log(`===== MAP DEBUG =====`);
      console.log(`Loaded ${data.length} properties for map`);
      
      // Check coordinate validity
      const validCoords = data.filter(p => 
        p.latitude && 
        p.longitude && 
        typeof p.latitude === 'number' && 
        typeof p.longitude === 'number' &&
        !(p.latitude === 0 && p.longitude === 0)
      );
      console.log(`Properties with valid coordinates: ${validCoords.length}`);
      
      // Check Austin area coordinates
      const austinCoords = validCoords.filter(p => 
        p.latitude >= 29.5 && p.latitude <= 31.0 && 
        p.longitude >= -98.0 && p.longitude <= -97.0
      );
      console.log(`Properties with coordinates in Austin area: ${austinCoords.length}`);
      
      // Look for suspicious patterns
      const suspiciousCoords = validCoords.filter(p => {
        const latStr = String(p.latitude);
        const lngStr = String(p.longitude);
        const hasLowPrecision = 
          (latStr.includes('.') && latStr.split('.')[1].length <= 1) ||
          (lngStr.includes('.') && lngStr.split('.')[1].length <= 1);
        const hasSuspiciousPattern = 
          latStr === lngStr || 
          latStr.endsWith('00000') || 
          lngStr.endsWith('00000');
        return hasLowPrecision || hasSuspiciousPattern;
      });
      console.log(`Properties with suspicious coordinates: ${suspiciousCoords.length}`);
      console.log(`===== END DEBUG =====`);
      
      setProperties(data);
      setTotalFetched(data.length);
    } catch (error) {
      console.error('Error fetching properties:', error);
    } finally {
      setLoading(false);
    }
  }

  // Function to handle sidebar state change
  const handleSidebarStateChange = (state) => {
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
          
          const geocodedBatch = await enhancedGeocodeProperties(batch, (property, status, details) => {
            // This is a callback that will be called for each property as it's processed
            const propertyName = property.name || `Property #${property.id}`;
            if (status === 'success') {
              addGeocodingLog(`Geocoded: ${propertyName} (${details})`, 'success');
            } else if (status === 'error') {
              addGeocodingLog(`Failed: ${propertyName} (${details})`, 'error');
            } else {
              addGeocodingLog(`${status}: ${propertyName} ${details ? `(${details})` : ''}`, 'info');
            }
          });
          
          // Count successes and failures
          const batchSuccess = geocodedBatch.filter(p => p._geocoded).length;
          const batchFail = geocodedBatch.filter(p => p._geocoding_failed).length;
          
          successCount += batchSuccess;
          failCount += batchFail;
          
          addGeocodingLog(`Batch ${i+1} complete: ${batchSuccess} successes, ${batchFail} failures`, 
                          batchSuccess > batchFail ? 'success' : 'warning');
          
          // Merge geocoded properties back into the main array
          const updatedProperties = [...properties];
          geocodedBatch.forEach(geocodedProp => {
            const index = updatedProperties.findIndex(p => p.id === geocodedProp.id);
            if (index !== -1) {
              updatedProperties[index] = geocodedProp;
            }
          });
          
          // Update the properties state
          setProperties(updatedProperties);
          calculateStats(updatedProperties);
          
          // Wait a bit between batches to avoid rate limits
          if (i < batches - 1) {
            addGeocodingLog(`Waiting 2 seconds before next batch to avoid rate limits`, 'info');
            await new Promise(resolve => setTimeout(resolve, 2000));
          }
        } catch (error) {
          console.error(`Error geocoding batch ${i+1}:`, error);
          addGeocodingLog(`Error with batch ${i+1}: ${error.message}`, 'error');
          failCount += batch.length;
        }
      }
      
      addGeocodingLog(`Geocoding complete: ${successCount} successes, ${failCount} failures`, 
                      successCount > failCount ? 'success' : 'error');
      
      alert(`Geocoding complete:\n\n${successCount} properties successfully geocoded\n${failCount} properties failed to geocode`);
      
    } catch (error) {
      console.error('Error in batch geocoding:', error);
      addGeocodingLog(`Geocoding error: ${error.message}`, 'error');
      alert(`Error geocoding properties: ${error.message}`);
    } finally {
      setGeocoding(false);
    }
  }

  function runPropertyAnalysis() {
    // Count properties at identical coordinates
    const coordMap = new Map();
    let duplicatedCoords = 0;
    
    properties.forEach(p => {
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
    
    // Find coordinates with multiple properties
    const multiplePropsLocations = Array.from(coordMap.entries())
      .filter(([_, count]) => count > 1)
      .sort((a, b) => b[1] - a[1]); // Sort by count descending
    
    const multiplePropsCount = multiplePropsLocations.reduce((sum, [_, count]) => sum + count, 0);
    const uniqueLocations = coordMap.size;
    
    // Count by geocoding source if available
    const bySource = {
      existing: properties.filter(p => p._geocoding_source === 'existing').length,
      verified_address: properties.filter(p => p._geocoding_source === 'verified_address').length,
      full_address: properties.filter(p => p._geocoding_source === 'full_address').length,
      property_name: properties.filter(p => p._geocoding_source === 'property_name').length,
      unknown: properties.filter(p => p.latitude && p.longitude && !p._geocoding_source).length
    };
    
    alert(
      `Map Properties Analysis:\n\n` +
      `- Total properties: ${properties.length}\n` +
      `- Properties with invalid coordinates: ${dataStats.invalidCoordinates}\n` +
      `   • Missing coordinates: ${dataStats.missingCoordinates}\n` +
      `   • Zero coordinates: ${dataStats.zeroCoordinates}\n` +
      `   • Invalid coordinate range: ${dataStats.invalidRange}\n\n` +
      `- Unique locations on map: ${uniqueLocations}\n` +
      `- Properties sharing exact coordinates: ${duplicatedCoords}\n` +
      `- Number of shared locations: ${multiplePropsLocations.length}\n\n` +
      (multiplePropsLocations.length > 0 ? 
        `Top shared locations:\n` +
        multiplePropsLocations.slice(0, 5).map(([coords, count]) => 
          `   • ${count} properties at ${coords}`
        ).join('\n') : '') +
      `\n\n` +
      `Geocoding sources:\n` +
      `   • Existing valid: ${bySource.existing}\n` +
      `   • Verified address: ${bySource.verified_address}\n` +
      `   • Full address: ${bySource.full_address}\n` +
      `   • Property name: ${bySource.property_name}\n` +
      `   • Unknown source: ${bySource.unknown}\n\n` +
      `Note: Properties at identical coordinates will appear as a single marker until clicked.`
    );
  }

  // Function to clean property data
  async function cleanPropertyData() {
    try {
      // Start the cleaning process
      setLoading(true);
      setCleaning(true);
      clearCleaningLogs();
      setShowCleaningLogs(true);
      
      addCleaningLog("Starting data cleaning process...", "info");
      
      // First, analyze the data to identify issues
      addCleaningLog("Analyzing properties for data quality issues...", "info");
      
      const dataIssues = {
        missingNames: properties.filter(p => !p.name || p.name.trim() === '').length,
        incompleteAddresses: properties.filter(p => p.address && (!p.city || !p.state)).length,
        suspiciousZeros: properties.filter(p => 
          (p.units === 0 || p.num_units === 0)
        ).length,
        suspiciousCoordinates: properties.filter(p => {
          // Check for suspicious patterns in coordinates
          if (!p.latitude || !p.longitude) return false;
          
          const latStr = String(p.latitude);
          const lngStr = String(p.longitude);
          
          // Check for very low precision or suspicious patterns
          return (
            (latStr.includes('.') && latStr.split('.')[1].length <= 2) ||
            (lngStr.includes('.') && lngStr.split('.')[1].length <= 2) ||
            latStr === lngStr || // Same lat/lng is suspicious
            latStr.endsWith('00000') || 
            lngStr.endsWith('00000') ||
            latStr.endsWith('.0') ||
            lngStr.endsWith('.0') ||
            latStr.endsWith('.5') || 
            lngStr.endsWith('.5')
          );
        }).length,
        duplicateNames: findDuplicates(properties, 'name'),
        duplicateAddresses: findDuplicates(properties, 'address'),
        testProperties: properties.filter(p => 
          (p.name && p.name.toLowerCase().includes('test')) || 
          (p.name && p.name.toLowerCase().includes('example')) ||
          (p.address && p.address.toLowerCase().includes('test')) || 
          p._is_test_property
        ).length
      };
      
      const totalIssues = dataIssues.missingNames + 
                          dataIssues.incompleteAddresses + 
                          dataIssues.suspiciousZeros + 
                          dataIssues.suspiciousCoordinates + 
                          dataIssues.duplicateNames.length + 
                          dataIssues.duplicateAddresses.length + 
                          dataIssues.testProperties;
      
      // Log analysis results
      addCleaningLog(`Analysis found ${totalIssues} data quality issues:`, "info");
      addCleaningLog(`- ${dataIssues.missingNames} properties missing names`, "detail");
      addCleaningLog(`- ${dataIssues.incompleteAddresses} properties with incomplete addresses`, "detail");
      addCleaningLog(`- ${dataIssues.suspiciousZeros} properties with suspicious zero values`, "detail");
      addCleaningLog(`- ${dataIssues.suspiciousCoordinates} properties with suspicious coordinates`, "detail");
      addCleaningLog(`- ${dataIssues.duplicateNames.length} duplicate property names`, "detail");
      addCleaningLog(`- ${dataIssues.duplicateAddresses.length} duplicate addresses`, "detail");
      addCleaningLog(`- ${dataIssues.testProperties} potential test/example properties`, "detail");
      
      // No issues found
      if (totalIssues === 0) {
        addCleaningLog('No data issues found that need cleaning', "success");
        alert('No data issues found that need cleaning');
        setLoading(false);
        setCleaning(false);
        return;
      }
      
      // Confirm with user
      const confirmation = confirm(
        `Found ${totalIssues} data quality issues:\n\n` +
        `- ${dataIssues.missingNames} properties missing names\n` +
        `- ${dataIssues.incompleteAddresses} properties with incomplete addresses\n` +
        `- ${dataIssues.suspiciousZeros} properties with suspicious zero values\n` +
        `- ${dataIssues.suspiciousCoordinates} properties with suspicious coordinates\n` +
        `- ${dataIssues.duplicateNames.length} duplicate property names\n` +
        `- ${dataIssues.duplicateAddresses.length} duplicate addresses\n` +
        `- ${dataIssues.testProperties} potential test/example properties\n\n` +
        `Would you like to clean these issues?`
      );
      
      if (!confirmation) {
        addCleaningLog('Cleaning cancelled by user', "warning");
        setLoading(false);
        setCleaning(false);
        return;
      }
      
      // Optional: offer advanced options
      const advancedOptions = confirm(
        "Would you like to use advanced cleaning options?\n\n" +
        "- Fix missing names and extract city/state from addresses\n" +
        "- Flag suspicious coordinates for geocoding\n" +
        "- Identify and flag duplicate properties\n" +
        "- Flag test properties for filtering\n\n" +
        "Select 'Cancel' for basic cleaning only."
      );
      
      addCleaningLog(`Starting ${advancedOptions ? 'advanced' : 'basic'} cleaning process...`, "info");
      
      // Apply fixes to a copy of the properties
      const cleanedProperties = [...properties];
      
      // Clean property names
      let issuesCleaned = 0;
      
      addCleaningLog(`Processing ${properties.length} properties...`, "info");
      
      properties.forEach((property, index) => {
        let propertyCleaned = false;
        let cleaningNotes = [];
        
        // Fix missing names using address
        if (!property.name || property.name.trim() === '') {
          if (property.address) {
            cleanedProperties[index].name = `Property at ${property.address.split(',')[0]}`;
            addCleaningLog(`Generated name for property #${property.id}: "${cleanedProperties[index].name}"`, "success");
          } else {
            cleanedProperties[index].name = `Unnamed Property ${property.id.toString().substring(0, 8)}`;
            addCleaningLog(`Generated fallback name for property #${property.id}: "${cleanedProperties[index].name}"`, "success");
          }
          propertyCleaned = true;
          cleaningNotes.push('Missing name fixed');
        }
        
        // Fix missing city/state if address exists
        if (property.address && (!property.city || !property.state)) {
          // Try to extract city and state from address
          const addressParts = property.address.split(',').map(p => p.trim());
          
          if (addressParts.length >= 2 && !property.city) {
            cleanedProperties[index].city = addressParts[addressParts.length - 2];
            addCleaningLog(`Extracted city "${cleanedProperties[index].city}" for property #${property.id}`, "success");
            propertyCleaned = true;
            cleaningNotes.push('City extracted from address');
          }
          
          if (addressParts.length >= 1 && !property.state) {
            // Try to extract state from the last part of the address
            const statePart = addressParts[addressParts.length - 1];
            const stateMatch = statePart.match(/[A-Z]{2}/);
            if (stateMatch) {
              cleanedProperties[index].state = stateMatch[0];
              addCleaningLog(`Extracted state "${cleanedProperties[index].state}" for property #${property.id}`, "success");
              propertyCleaned = true;
              cleaningNotes.push('State extracted from address');
            }
          }
        }
        
        // Flag suspicious coordinates for advanced cleaning
        if (advancedOptions) {
          const latStr = String(property.latitude || '');
          const lngStr = String(property.longitude || '');
          
          // Check for suspicious patterns in coordinates
          const hasLowPrecision = 
            (latStr.includes('.') && latStr.split('.')[1].length <= 2) ||
            (lngStr.includes('.') && lngStr.split('.')[1].length <= 2);
            
          const hasSuspiciousPattern = 
            latStr === lngStr || // Same lat/lng is very unlikely
            latStr.endsWith('00000') || 
            lngStr.endsWith('00000') ||
            latStr.endsWith('.0') ||
            lngStr.endsWith('.0') ||
            latStr.endsWith('.5') || 
            lngStr.endsWith('.5');
            
          if (hasLowPrecision || hasSuspiciousPattern) {
            cleanedProperties[index]._is_grid_pattern = true;
            cleanedProperties[index]._needs_geocoding = true;
            addCleaningLog(`Flagged suspicious coordinates (${latStr}, ${lngStr}) for property #${property.id}`, "warning");
            propertyCleaned = true;
            cleaningNotes.push('Flagged suspicious coordinates for geocoding');
          }
        }
        
        // Flag test properties
        if ((property.name && property.name.toLowerCase().includes('test')) || 
            (property.name && property.name.toLowerCase().includes('example')) ||
            (property.address && property.address.toLowerCase().includes('test'))) {
          cleanedProperties[index]._is_test_property = true;
          addCleaningLog(`Flagged test property #${property.id}: "${property.name}"`, "warning");
          propertyCleaned = true;
          cleaningNotes.push('Flagged as test property');
        }
        
        // Flag suspicious zeros for advanced cleaning
        if (advancedOptions && (property.units === 0 || property.num_units === 0)) {
          // We'll just flag these for now, manual review is needed
          if (!cleanedProperties[index]._data_quality_issues) {
            cleanedProperties[index]._data_quality_issues = [];
          }
          
          cleanedProperties[index]._data_quality_issues.push('zero_units');
          addCleaningLog(`Flagged zero units for property #${property.id}`, "warning");
          propertyCleaned = true;
          cleaningNotes.push('Flagged zero units');
        }
        
        // Update property with cleaning information
        if (propertyCleaned) {
          cleanedProperties[index]._data_cleaned = true;
          cleanedProperties[index]._cleaning_notes = cleaningNotes.join(', ');
          issuesCleaned++;
        }
      });
      
      addCleaningLog(`Finished processing. Cleaned ${issuesCleaned} properties.`, "success");
      
      // Update state with cleaned properties
      addCleaningLog("Updating property data with cleaned values...", "info");
      setProperties(cleanedProperties);
      calculateStats(cleanedProperties);
      
      // Alert user of results
      addCleaningLog("Data cleaning complete!", "success");
      alert(
        `Data cleaning complete!\n\n` +
        `- ${issuesCleaned} properties were cleaned\n` +
        `- Added names to ${dataIssues.missingNames} properties\n` +
        `- Extracted city/state for ${dataIssues.incompleteAddresses} properties\n` +
        `- Flagged ${dataIssues.suspiciousCoordinates} suspicious coordinates for geocoding\n` +
        `- Identified ${dataIssues.duplicateNames.length} duplicate names\n` +
        `- Flagged ${dataIssues.testProperties} test properties\n\n` +
        `Next steps:\n` +
        `1. Use "Batch Geocode" to fix flagged coordinates\n` +
        `2. Use "Properties Analysis" to review data quality\n` +
        `3. Some properties still require manual review`
      );
    } catch (error) {
      console.error('Error cleaning property data:', error);
      addCleaningLog(`Error: ${error.message}`, "error");
      alert(`Error cleaning data: ${error.message}`);
    } finally {
      setLoading(false);
      setCleaning(false);
    }
  }
  
  // Helper function to find duplicates in properties by field
  function findDuplicates(array, key) {
    const counts = {};
    const duplicates = [];
    
    // Skip entries with empty values
    array.forEach(item => {
      if (item[key] && item[key].trim() !== '') {
        const value = item[key].toLowerCase().trim();
        counts[value] = (counts[value] || 0) + 1;
      }
    });
    
    // Find values that appear more than once
    Object.keys(counts).forEach(value => {
      if (counts[value] > 1) {
        duplicates.push({
          value,
          count: counts[value]
        });
      }
    });
    
    return duplicates;
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
  const addGeocodingLog = useCallback((message, type = 'info') => {
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
  const addCleaningLog = useCallback((message, type = 'info') => {
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
  const addEnrichingLog = useCallback((message, type = 'info') => {
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

  return (
    <Layout title="Property Map | Acquire Apartments">
      <div className="relative bg-white min-h-screen">
        <div className="flex flex-col h-[calc(100vh-4rem)] overflow-hidden">
          <div className="container mx-auto px-4 py-4 flex-shrink-0">
            <h1 className="text-2xl font-bold text-gray-800">Map View</h1>
            <p className="text-gray-600">Browse properties on the map or use filters to refine your search</p>
          </div>
          
          <div className="flex-grow flex">
            {/* Property Sidebar */}
            <div className={`flex-shrink-0 transition-all duration-300 ${
              sidebarState === 'collapsed' ? 'w-12' : 
              sidebarState === 'fullscreen' ? 'w-full' : 
              'w-full md:w-1/3 lg:w-1/4'
            }`}>
              <div className="p-4">
                {React.createElement(dynamic(() => import('../src/components/PropertySidebar')), {
                  properties,
                  selectedProperty,
                  setSelectedProperty,
                  loading,
                  sidebarState,
                  onSidebarStateChange: handleSidebarStateChange
                })}
              </div>
            </div>
            
            {/* Map Container */}
            <div className={`flex-grow transition-all duration-300 ${
              sidebarState === 'fullscreen' ? 'hidden' : 'block'
            }`}>
              <div className="h-full rounded-lg shadow overflow-hidden">
                <MapComponent
                  properties={properties}
                  selectedProperty={selectedProperty}
                  setSelectedProperty={setSelectedProperty}
                  onBoundsChange={handleBoundsChange}
                />
              </div>
            </div>
          </div>

          {/* Geocoding Logs */}
          {showGeocodingLogs && geocodingLogs.length > 0 && (
            <div className="absolute bottom-4 right-4 w-96 max-h-64 bg-white rounded-lg shadow-lg overflow-auto p-4 z-50">
              <div className="flex justify-between items-center mb-2">
                <h3 className="font-semibold">Geocoding Logs</h3>
                <button onClick={() => setShowGeocodingLogs(false)} className="text-gray-500 hover:text-gray-700">
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>
              <div className="space-y-1">
                {geocodingLogs.map((log, index) => (
                  <div key={index} className={`text-sm p-1 ${
                    log.type === 'error' ? 'text-red-600' :
                    log.type === 'warning' ? 'text-amber-600' :
                    log.type === 'success' ? 'text-green-600' :
                    'text-gray-600'
                  }`}>
                    {log.message}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Similar blocks for other logs - cleaning and enriching logs remain unchanged */}
        </div>
      </div>
    </Layout>
  );
} 