import { useEffect, useState, useCallback } from 'react';
import dynamic from 'next/dynamic';
import { useRouter } from 'next/router';
import Script from 'next/script';
import Layout from '../components/Layout';
import PropertySidebar from '../components/PropertySidebar';
import PropertyDetails from '../components/PropertyDetails';
import PropertyFilter from '../components/PropertyFilter';
import RealTimeUpdates from '../components/RealTimeUpdates';
import { FilterProvider, useFilter } from '../contexts/FilterContext';
import { useTheme } from '../contexts/ThemeContext';
import { Property } from '../types/property';
import { fetchProperties, createTestProperty } from '../../lib/supabase';
import { supabase } from '../../lib/supabase';
import { triggerBatchGeocode, getGeocodingStats } from '../utils/geocodingApi';

// Add Google Maps type declaration
declare global {
  interface Window {
    google?: {
      maps: {
        Geocoder: new () => {
          geocode: (
            request: { address: string },
            callback: (
              results: Array<{
                geometry: {
                  location: {
                    lat: () => number;
                    lng: () => number;
                  }
                }
              }>,
              status: string
            ) => void
          ) => void;
        }
      }
    }
  }
}

// Import the map component dynamically to avoid SSR issues with Leaflet
const MapComponent = dynamic(() => import('../components/MapComponent'), {
  ssr: false,
  loading: () => (
    <div className="h-[80vh] lg:h-[85vh] bg-gray-200 dark:bg-gray-800 rounded-lg flex items-center justify-center">
      <div className="text-center">
        <svg
          className="animate-spin h-8 w-8 text-gray-500 dark:text-gray-400 mx-auto mb-2"
          xmlns="http://www.w3.org/2000/svg"
          fill="none"
          viewBox="0 0 24 24"
        >
          <circle
            className="opacity-25"
            cx="12"
            cy="12"
            r="10"
            stroke="currentColor"
            strokeWidth="4"
          ></circle>
          <path
            className="opacity-75"
            fill="currentColor"
            d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
          ></path>
        </svg>
        <p className="dark:text-gray-300">Loading map...</p>
      </div>
    </div>
  )
});

// Add this new component for admin controls
const AdminControls = ({ onTriggerGeocode }) => {
  const [isAdmin, setIsAdmin] = useState(false);
  const [stats, setStats] = useState(null);
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    // Check if the user is logged in
    const checkAdmin = async () => {
      const { data: { session } } = await supabase.auth.getSession();
      setIsAdmin(!!session);
    };
    
    checkAdmin();
  }, []);

  useEffect(() => {
    // If user is admin, fetch geocoding stats
    if (isAdmin) {
      fetchStats();
    }
  }, [isAdmin]);

  const fetchStats = async () => {
    try {
      setIsLoading(true);
      const geocodingStats = await getGeocodingStats();
      setStats(geocodingStats);
    } catch (error) {
      console.error('Failed to fetch geocoding stats:', error);
    } finally {
      setIsLoading(false);
    }
  };

  if (!isAdmin) return null;

  return (
    <div className="mb-4 p-3 border rounded-lg bg-white shadow-sm">
      <h3 className="text-md font-semibold mb-2">Admin Controls</h3>
      {stats && (
        <div className="text-sm mb-2">
          <p className="mb-1">
            Properties with coordinates: <span className="font-medium">{stats.properties_with_coordinates}</span> 
            <span className="text-gray-500 ml-1">({stats.geocoded_percentage}%)</span>
          </p>
          <p className="mb-1">
            Properties without coordinates: <span className="font-medium">{stats.properties_without_coordinates}</span>
          </p>
        </div>
      )}
      <div className="flex gap-2">
        <button
          className="px-3 py-1 text-xs bg-blue-500 text-white rounded hover:bg-blue-600 disabled:opacity-50"
          onClick={onTriggerGeocode}
          disabled={isLoading || !stats || stats.properties_without_coordinates === 0}
        >
          {isLoading ? 'Loading...' : 'Trigger Batch Geocoding'}
        </button>
        <button
          className="px-3 py-1 text-xs bg-gray-200 text-gray-800 rounded hover:bg-gray-300"
          onClick={fetchStats}
          disabled={isLoading}
        >
          Refresh Stats
        </button>
      </div>
    </div>
  );
};

// Main content of the map page, wrapped by providers
const MapPageContent = () => {
  // State
  const [properties, setProperties] = useState<Property[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedProperty, setSelectedProperty] = useState<Property | null>(null);
  const [showDetails, setShowDetails] = useState(false);
  const [showFilter, setShowFilter] = useState(false);
  const [mapBounds, setMapBounds] = useState(null);
  const { filters } = useFilter();
  const { isDarkMode, toggleTheme } = useTheme();
  const router = useRouter();
  const [error, setError] = useState<string | null>(null);
  const [totalProperties, setTotalProperties] = useState(0);
  
  // Get Mapbox token from environment
  const mapboxToken = process.env.NEXT_PUBLIC_MAPBOX_ACCESS_TOKEN;

  // On first load, check if there's a propertyId in the URL
  useEffect(() => {
    const { propertyId } = router.query;
    if (propertyId && typeof propertyId === 'string') {
      // Find the property and select it
      const fetchPropertyById = async () => {
        try {
          // We'll fetch all properties since we need them for the map anyway
          // A real optimization would be to fetch just this one property separately
          const data = await fetchProperties({
            filters: { id: propertyId },
            includeResearch: true, // Include property research data with valid coordinates
            page: 1,
            pageSize: 10,
            sortBy: 'created_at',
            sortAsc: false,
            includeIncomplete: true
          });
          
          if (data && data.length > 0) {
            setSelectedProperty(data[0]);
            setShowDetails(true);
          }
        } catch (error) {
          console.error('Error fetching property by ID:', error);
        }
      };
      
      fetchPropertyById();
    }
  }, [router.query]);

  // Fetch properties when filters change
  useEffect(() => {
    loadProperties();
  }, [filters]);

  const loadProperties = async () => {
    try {
      setLoading(true);
      setError(null);
      
      // Convert filter state to API parameters
      const apiFilters: Record<string, any> = {};
      
      // Add text search
      if (filters.search) {
        // Search in name and address
        apiFilters.or = `name.ilike.%${filters.search}%,address.ilike.%${filters.search}%`;
      }
      
      // Add status filter
      if (filters.status) {
        apiFilters.status = filters.status;
      }
      
      // Add price range
      if (filters.min_price) {
        apiFilters.price_gte = filters.min_price;
      }
      if (filters.max_price) {
        apiFilters.price_lte = filters.max_price;
      }
      
      // Add units range
      if (filters.min_units) {
        apiFilters.or = `${apiFilters.or ? apiFilters.or + ',' : ''}units.gte.${filters.min_units},num_units.gte.${filters.min_units}`;
      }
      if (filters.max_units) {
        apiFilters.or = `${apiFilters.or ? apiFilters.or + ',' : ''}units.lte.${filters.max_units},num_units.lte.${filters.max_units}`;
      }
      
      // Add year built range
      if (filters.year_built_min) {
        apiFilters.year_built_gte = filters.year_built_min;
      }
      if (filters.year_built_max) {
        apiFilters.year_built_lte = filters.year_built_max;
      }
      
      // Add location filters
      if (filters.city) {
        apiFilters.city = filters.city;
      }
      if (filters.state) {
        apiFilters.state = filters.state;
      }
      
      // First try to load properties with valid coordinates only
      const fetchOptions = {
        filters: apiFilters,
        page: filters.page || 1,
        pageSize: filters.limit || 500,
        sortBy: filters.sort_by || 'created_at',
        sortAsc: filters.sort_dir === 'asc',
        includeResearch: true, // Always include research data to get better coordinates
        includeIncomplete: false // Initially, only fetch properties with coordinates
      };
      
      console.log('Fetching properties with valid coordinates:', fetchOptions);
      
      const propertiesWithCoordinates = await fetchProperties(fetchOptions);
      
      // If we got properties with coordinates, use them
      if (propertiesWithCoordinates && propertiesWithCoordinates.length > 0) {
        console.log(`Found ${propertiesWithCoordinates.length} properties with valid coordinates`);
        setProperties(propertiesWithCoordinates);
        setTotalProperties(propertiesWithCoordinates.length);
        setLoading(false);
        return;
      }
      
      // If no properties with coordinates were found, try without the coordinate filter
      console.log('No properties with coordinates found, fetching all properties');
      
      const allFetchOptions = {
        ...fetchOptions,
        includeIncomplete: true
      };
      
      const allProperties = await fetchProperties(allFetchOptions);
      
      if (allProperties && allProperties.length > 0) {
        console.log(`Found ${allProperties.length} total properties, but many may lack coordinates`);
        setProperties(allProperties);
        setTotalProperties(allProperties.length);
      } else {
        console.log('No properties found at all');
        setProperties([]);
        setTotalProperties(0);
      }
    } catch (err) {
      console.error('Error loading properties:', err);
      setError('Failed to load properties. Please try again.');
      setProperties([]);
    } finally {
      setLoading(false);
    }
  };
  
  // Handle property selection
  const handlePropertySelect = (property: Property | null) => {
    setSelectedProperty(property);
    if (property) {
      setShowDetails(true);
      
      // Update URL with property ID for sharing
      router.push({
        pathname: '/map',
        query: { propertyId: property.id }
      }, undefined, { shallow: true });
    } else {
      // Remove property ID from URL
      router.push('/map', undefined, { shallow: true });
    }
  };
  
  // Handle map bounds change
  const handleBoundsChange = (bounds: any) => {
    setMapBounds(bounds);
  };
  
  // Handle real-time property updates
  const handlePropertyUpdate = useCallback((updatedProperty: Property) => {
    setProperties(prevProperties => {
      // Find and replace the updated property
      const index = prevProperties.findIndex(p => p.id === updatedProperty.id);
      if (index !== -1) {
        const updatedProperties = [...prevProperties];
        updatedProperties[index] = updatedProperty;
        return updatedProperties;
      }
      return prevProperties;
    });
    
    // Update selected property if it's the one that was updated
    if (selectedProperty?.id === updatedProperty.id) {
      setSelectedProperty(updatedProperty);
    }
  }, [selectedProperty]);
  
  // Handle new property creation
  const handlePropertyCreate = useCallback((newProperty: Property) => {
    setProperties(prevProperties => [newProperty, ...prevProperties]);
  }, []);
  
  // Toggle dark mode
  const handleToggleDarkMode = () => {
    toggleTheme();
  };
  
  // Get Google Maps API key from environment
  const googleMapsApiKey = process.env.NEXT_PUBLIC_GOOGLE_MAPS_API_KEY;

  // Add a new function to handle triggering the geocoding
  const handleTriggerGeocode = async () => {
    try {
      const batchSize = 100; // Process a reasonable batch
      
      // Show confirmation dialog
      if (window.confirm(`Start batch geocoding for up to ${batchSize} properties?`)) {
        const result = await triggerBatchGeocode(batchSize);
        
        alert(`Batch geocoding started. Task ID: ${result.task_id}`);
        console.log('Batch geocoding triggered:', result);
      }
    } catch (error) {
      console.error('Failed to trigger batch geocoding:', error);
      alert('Failed to trigger batch geocoding. See console for details.');
    }
  };

  return (
    <Layout title="Interactive Map | Austin Multifamily Property Map">
      {/* Load Google Maps API for geocoding */}
      {googleMapsApiKey && (
        <Script
          src={`https://maps.googleapis.com/maps/api/js?key=${googleMapsApiKey}&libraries=places`}
          strategy="beforeInteractive"
        />
      )}
      <div className="container mx-auto relative">
        {/* Admin link for developers */}
        <div className="absolute top-4 left-4 z-10 flex flex-col space-y-1">
          <a href="/admin/geocoding" className="text-xs text-gray-500 dark:text-gray-400 hover:underline">
            Admin: Geocoding Dashboard
          </a>
          <a href="/admin/sync-coordinates" className="text-xs text-gray-500 dark:text-gray-400 hover:underline">
            Admin: Fix Map Coordinates
          </a>
          <button 
            onClick={async () => {
              try {
                // First, check if we can connect to Supabase
                const { data: tableInfo, error: tableError } = await supabase
                  .from('properties')
                  .select('*', { count: 'exact', head: true });
                  
                if (tableError) {
                  console.error('Supabase connection error:', tableError);
                  alert(`Supabase connection error: ${tableError.message}`);
                  return;
                }
                
                // Perform a direct count query to get the total number of rows
                const { count, error: countError } = await supabase
                  .from('properties')
                  .select('*', { count: 'exact', head: true });
                  
                if (countError) {
                  console.error('Error counting properties:', countError);
                  alert(`Error counting properties: ${countError.message}`);
                  return;
                }
                
                console.log('Total properties in database:', count);
                
                // Now, examine the table structure
                try {
                  // Try to fetch one row just to see columns
                  const { data: sample, error: sampleError } = await supabase
                    .from('properties')
                    .select('*')
                    .limit(1);
                    
                  if (sampleError) {
                    alert(`Database connected! Error getting sample: ${sampleError.message}. Total rows: ${count}`);
                  } else if (sample && sample.length > 0) {
                    const columnList = Object.keys(sample[0]).join(', ');
                    alert(`Database connected! Found ${count} total properties. Sample from row 1 of ${count}. \nColumns: ${columnList}`);
                    console.log('Sample property:', sample[0]);
                  } else {
                    alert(`Database connected! Found ${count} total properties, but unable to retrieve a sample row.`);
                  }
                } catch (schemaErr) {
                  console.error('Error checking schema:', schemaErr);
                  
                  // Fallback to simple count
                  alert(`Database connected! Found ${count} total properties. (Unable to inspect schema)`);
                }
              } catch (err) {
                console.error('Error checking database:', err);
                alert(`Database error: ${err instanceof Error ? err.message : String(err)}`);
              }
            }}
            className="text-xs text-blue-500 dark:text-blue-400 hover:underline"
          >
            Check Database Connection
          </button>
          <button 
            onClick={async () => {
              try {
                if (confirm('Create a test property in the database?')) {
                  const result = await createTestProperty();
                  alert(`Test property created! ${result.info || ''} Refresh the page to see it.`);
                  console.log('Test property created:', result.data);
                }
              } catch (err) {
                console.error('Error creating test property:', err);
                alert(`Error creating test property: ${err instanceof Error ? err.message : String(err)}`);
              }
            }}
            className="text-xs text-green-500 dark:text-green-400 hover:underline"
          >
            Create Test Property
          </button>
          <button 
            onClick={async () => {
              try {
                // Run step-by-step diagnostics
                alert("Starting diagnostic checks - check console for detailed output");
                console.log("=== PROPERTY DIAGNOSTIC CHECKS ===");
                
                // Step 1: Count properties
                const { count, error: countError } = await supabase
                  .from('properties')
                  .select('*', { count: 'exact', head: true });
                  
                if (countError) {
                  console.error('Error counting properties:', countError);
                  alert(`Error counting properties: ${countError.message}`);
                  return;
                }
                
                console.log(`Total properties in database: ${count}`);
                
                // Step 2: Check for properties with coordinates
                const { data: withCoords, error: coordsError } = await supabase
                  .from('properties')
                  .select('id, name, latitude, longitude')
                  .not('latitude', 'is', null)
                  .not('longitude', 'is', null);
                  
                if (coordsError) {
                  console.error('Error checking coordinates:', coordsError);
                } else {
                  console.log(`Properties with coordinates: ${withCoords?.length || 0} of ${count}`);
                  console.log('Sample with coordinates:', withCoords?.slice(0, 3));
                  
                  // Step 2.1: Check for zero coordinates
                  const zeroCoords = withCoords?.filter(p => 
                    p.latitude === 0 || p.longitude === 0 ||
                    p.latitude === null || p.longitude === null
                  );
                  console.log(`Properties with zero/null coordinates: ${zeroCoords?.length || 0}`);
                  
                  // Step 2.2: Check for coordinates outside of reasonable ranges
                  const invalidRangeCoords = withCoords?.filter(p => 
                    p.latitude < -90 || p.latitude > 90 ||
                    p.longitude < -180 || p.longitude > 180
                  );
                  console.log(`Properties with invalid coordinate ranges: ${invalidRangeCoords?.length || 0}`);
                  
                  // Step 2.3: Check for coordinates outside of Austin area
                  const outsideAustinCoords = withCoords?.filter(p => 
                    !(p.latitude >= 29.5 && p.latitude <= 31.0 && 
                      p.longitude >= -98.0 && p.longitude <= -97.0)
                  );
                  console.log(`Properties with coordinates outside Austin area: ${outsideAustinCoords?.length || 0}`);
                }
                
                // Step 3: Check property types
                const { data: propertyData, error: propertyDataError } = await supabase
                  .from('properties')
                  .select('property_type')
                  .not('property_type', 'is', null);
                  
                if (propertyDataError) {
                  console.error('Error checking property types:', propertyDataError);
                } else {
                  // Manually count the different property types
                  const typeCounts = {};
                  propertyData.forEach(p => {
                    const type = p.property_type;
                    typeCounts[type] = (typeCounts[type] || 0) + 1;
                  });
                  console.log('Property types:', typeCounts);
                }
                
                // Step 4: Check status values - try both field names
                // First try property_status
                const { data: statusData, error: statusDataError } = await supabase
                  .from('properties')
                  .select('property_status')
                  .not('property_status', 'is', null);
                  
                if (statusDataError) {
                  console.error('Error checking property_status field:', statusDataError);
                } else {
                  // Manually count the different statuses
                  const statusCounts = {};
                  statusData.forEach(p => {
                    const status = p.property_status;
                    statusCounts[status] = (statusCounts[status] || 0) + 1;
                  });
                  console.log('Property statuses (property_status field):', statusCounts);
                }
                
                // Try alternate field name 'status'
                const { data: altStatusData, error: altStatusDataError } = await supabase
                  .from('properties')
                  .select('status')
                  .not('status', 'is', null);
                  
                if (altStatusDataError) {
                  console.error('Error checking status field:', altStatusDataError);
                } else {
                  // Manually count the different statuses
                  const altStatusCounts = {};
                  altStatusData.forEach(p => {
                    const status = p.status;
                    altStatusCounts[status] = (altStatusCounts[status] || 0) + 1;
                  });
                  console.log('Property statuses (status field):', altStatusCounts);
                }
                
                // Step 5: Get sample real properties (not test ones)
                const { data: realProperties, error: realError } = await supabase
                  .from('properties')
                  .select('*')
                  .not('name', 'ilike', '%test%')
                  .not('name', 'ilike', '%example%')
                  .not('name', 'ilike', '%sample%')
                  .limit(5);
                  
                if (realError) {
                  console.error('Error fetching real properties:', realError);
                } else {
                  console.log('Sample real properties:', realProperties);
                }
                
                alert(`Diagnostic complete! Check the console for detailed results. Found ${count} total properties in the database.`);
              } catch (err) {
                console.error('Diagnostic error:', err);
                alert(`Diagnostic error: ${err instanceof Error ? err.message : String(err)}`);
              }
            }}
            className="text-xs text-orange-500 dark:text-orange-400 hover:underline"
          >
            Run Diagnostics
          </button>
          <button
            onClick={() => {
              if (!selectedProperty) {
                alert("Please select a property first");
                return;
              }
              
              if (confirm(`Try to geocode the selected property: "${selectedProperty.name}"?`)) {
                // Use the browser's geocoding API if available
                const googleMaps = window.google?.maps;
                if (googleMaps && googleMaps.Geocoder) {
                  const geocoder = new googleMaps.Geocoder();
                  
                  // Build address string
                  const address = `${selectedProperty.address}, ${selectedProperty.city}, ${selectedProperty.state}`;
                  
                  geocoder.geocode({ address }, async (results, status) => {
                    if (status === "OK" && results && results[0] && results[0].geometry) {
                      const lat = results[0].geometry.location.lat();
                      const lng = results[0].geometry.location.lng();
                      
                      console.log(`Geocoded "${address}" to [${lat}, ${lng}]`);
                      
                      // Update the property in the state
                      const updatedProperty = { 
                        ...selectedProperty, 
                        latitude: lat, 
                        longitude: lng,
                        _coordinates_missing: false,
                        _needs_geocoding: false,
                        _is_grid_pattern: false,
                        _is_invalid_range: false,
                        _coordinates_from_research: false,
                        _outside_austin: false,
                        _geocoded: true
                      };
                      
                      setSelectedProperty(updatedProperty);
                      
                      // Update the properties list
                      setProperties(prevProperties => 
                        prevProperties.map(p => 
                          p.id === selectedProperty.id ? updatedProperty : p
                        )
                      );
                      
                      // Optional - actually update in database
                      if (confirm(`Success! Update these coordinates in the database?\nLatitude: ${lat}\nLongitude: ${lng}`)) {
                        const { error } = await supabase
                          .from('properties')
                          .update({ latitude: lat, longitude: lng })
                          .eq('id', selectedProperty.id);
                          
                        if (error) {
                          console.error('Error updating coordinates in database:', error);
                          alert(`Error updating database: ${error.message}`);
                        } else {
                          alert('Coordinates updated in database');
                        }
                      }
                    } else {
                      console.error('Geocoding failed:', status);
                      alert(`Geocoding failed: ${status}`);
                    }
                  });
                } else {
                  alert("Google Maps Geocoding API not available");
                }
              }
            }}
            className="text-xs text-purple-500 dark:text-purple-400 hover:underline"
          >
            Geocode Selected
          </button>
          <button
            onClick={() => {
              // Function to identify properties with problematic coordinates
              const allProperties = [...properties];
              
              // Reset any previous highlighting
              setProperties(allProperties.map(p => ({
                ...p,
                _highlight: false
              })));
              
              const problemProperties = allProperties.filter(p => {
                // Missing coordinates
                if (!p.latitude || !p.longitude) return true;
                
                // Zero coordinates
                if (p.latitude === 0 || p.longitude === 0) return true;
                
                // Invalid ranges
                if (p.latitude < -90 || p.latitude > 90 || 
                    p.longitude < -180 || p.longitude > 180) return true;
                
                // Outside Austin area (approximate)
                if (!(p.latitude >= 29.5 && p.latitude <= 31.0 && 
                     p.longitude >= -98.0 && p.longitude <= -97.0)) return true;
                
                // No other issues detected
                return false;
              });
              
              // Highlight the problem properties
              if (problemProperties.length > 0) {
                const highlightedProperties = allProperties.map(p => ({
                  ...p,
                  _highlight: problemProperties.some(pp => pp.id === p.id)
                }));
                
                setProperties(highlightedProperties);
                
                alert(`Found ${problemProperties.length} properties with coordinate issues. They are now highlighted in the list.`);
                console.log('Properties with coordinate issues:', problemProperties);
              } else {
                alert('No properties with coordinate issues found.');
              }
            }}
            className="text-xs text-blue-500 dark:text-blue-400 hover:underline"
          >
            Check Coordinates
          </button>
        </div>
        
        {/* Dark mode toggle and filter toggle buttons */}
        <div className="absolute top-4 right-4 z-10 flex space-x-2">
          <button
            onClick={handleToggleDarkMode}
            className="p-2 rounded-full bg-white dark:bg-gray-800 shadow-md"
            aria-label="Toggle dark mode"
          >
            {isDarkMode ? (
              <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 text-yellow-500" viewBox="0 0 20 20" fill="currentColor">
                <path fillRule="evenodd" d="M10 2a1 1 0 011 1v1a1 1 0 11-2 0V3a1 1 0 011-1zm4 8a4 4 0 11-8 0 4 4 0 018 0zm-.464 4.95l.707.707a1 1 0 001.414-1.414l-.707-.707a1 1 0 00-1.414 1.414zm2.12-10.607a1 1 0 010 1.414l-.706.707a1 1 0 11-1.414-1.414l.707-.707a1 1 0 011.414 0zM17 11a1 1 0 100-2h-1a1 1 0 100 2h1zm-7 4a1 1 0 011 1v1a1 1 0 11-2 0v-1a1 1 0 011-1zM5.05 6.464A1 1 0 106.465 5.05l-.708-.707a1 1 0 00-1.414 1.414l.707.707zm1.414 8.486l-.707.707a1 1 0 01-1.414-1.414l.707-.707a1 1 0 011.414 1.414zM4 11a1 1 0 100-2H3a1 1 0 000 2h1z" clipRule="evenodd" />
              </svg>
            ) : (
              <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 text-gray-700" viewBox="0 0 20 20" fill="currentColor">
                <path d="M17.293 13.293A8 8 0 016.707 2.707a8.001 8.001 0 1010.586 10.586z" />
              </svg>
            )}
          </button>
          
          <button
            onClick={() => setShowFilter(!showFilter)}
            className={`p-2 rounded-full shadow-md ${
              isDarkMode ? 'bg-gray-800 text-white' : 'bg-white text-gray-700'
            } ${showFilter ? 'border-2 border-blue-500' : ''}`}
            aria-label="Toggle filter panel"
          >
            <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
              <path fillRule="evenodd" d="M3 3a1 1 0 011-1h12a1 1 0 011 1v3a1 1 0 01-.293.707L12 11.414V15a1 1 0 01-.293.707l-2 2A1 1 0 018 17v-5.586L3.293 6.707A1 1 0 013 6V3z" clipRule="evenodd" />
            </svg>
          </button>
        </div>
        
        {/* Filter panel - shown only when filter toggle is active */}
        {showFilter && (
          <div className="absolute top-16 right-4 z-10 w-72 md:w-80">
            <PropertyFilter 
              onApplyFilter={() => {}} // Filters are automatically applied via context
            />
          </div>
        )}
        
        <div className="flex flex-col lg:flex-row gap-4 py-4">
          {/* Left sidebar - property list */}
          <div className={`lg:w-1/3 ${showDetails ? 'hidden lg:block' : ''}`}>
            <PropertySidebar
              properties={properties}
              selectedProperty={selectedProperty}
              setSelectedProperty={handlePropertySelect}
              loading={loading}
            />
          </div>
          
          {/* Property details panel (mobile: replaces sidebar, desktop: replaces map) */}
          {showDetails && (
            <div className="lg:w-1/3 lg:hidden">
              <PropertyDetails
                property={selectedProperty!}
                onClose={() => {
                  setShowDetails(false);
                  setSelectedProperty(null);
                  router.push('/map', undefined, { shallow: true });
                }}
              />
            </div>
          )}
          
          {/* Map container */}
          <div className={`${showDetails ? 'hidden lg:block' : ''} lg:flex-1`}>
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-xl font-semibold">Interactive Map</h2>
              <button
                onClick={handleToggleDarkMode}
                className="p-2 rounded bg-gray-200 dark:bg-gray-700 text-gray-800 dark:text-gray-200"
                title="Toggle dark mode"
              >
                {isDarkMode ? (
                  <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z" />
                  </svg>
                ) : (
                  <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z" />
                  </svg>
                )}
              </button>
            </div>
            
            {/* Display error message if any */}
            {error && (
              <div className="mb-4 p-3 border-l-4 border-red-500 bg-red-50 dark:bg-red-900/20 text-red-700 dark:text-red-400">
                <div className="flex items-center">
                  <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  <span>{error}</span>
                </div>
              </div>
            )}
            
            {/* Property count info */}
            {!loading && properties.length > 0 && (
              <div className="mb-4 text-sm text-gray-600 dark:text-gray-400">
                Showing {properties.length} {properties.length === 1 ? 'property' : 'properties'}
                {totalProperties > properties.length && ` with coordinates (${totalProperties} total)`}
              </div>
            )}

            <MapComponent 
              properties={properties} 
              selectedProperty={selectedProperty}
              setSelectedProperty={handlePropertySelect}
              onBoundsChange={handleBoundsChange}
              mapboxToken={mapboxToken}
            />
          </div>
          
          {/* Property details panel (desktop: third column) */}
          {showDetails && selectedProperty && (
            <div className="hidden lg:block lg:w-1/3">
              <PropertyDetails
                property={selectedProperty}
                onClose={() => {
                  setShowDetails(false);
                  setSelectedProperty(null);
                  router.push('/map', undefined, { shallow: true });
                }}
              />
            </div>
          )}
        </div>
      </div>
      
      {/* Real-time updates component */}
      <RealTimeUpdates
        onPropertyUpdate={handlePropertyUpdate}
        onPropertyCreate={handlePropertyCreate}
      />
      
      {/* Add the AdminControls component here, before the filters */}
      <AdminControls onTriggerGeocode={handleTriggerGeocode} />
    </Layout>
  );
};

// Wrap the MapPageContent with providers
export default function MapPage() {
  return (
    <FilterProvider>
      <MapPageContent />
    </FilterProvider>
  );
}