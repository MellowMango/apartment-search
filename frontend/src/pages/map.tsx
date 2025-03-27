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

// New component for admin-only sidebar links
const AdminSidebarLinks = ({ properties, setProperties }) => {
  const [isAdmin, setIsAdmin] = useState(false);

  useEffect(() => {
    // Check if the user is logged in
    const checkAdmin = async () => {
      const { data: { session } } = await supabase.auth.getSession();
      setIsAdmin(!!session);
    };
    
    checkAdmin();
  }, []);

  if (!isAdmin) return null;

  // Function to highlight properties with coordinate issues
  const checkCoordinateIssues = () => {
    // Function to identify properties with problematic coordinates
    const allProperties = [...properties];
    
    // Reset any previous highlighting
    const resetProperties = allProperties.map(p => ({
      ...p,
      _highlight: false
    }));
    
    setProperties(resetProperties);
    
    const problemProperties = resetProperties.filter(p => {
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
      const highlightedProperties = resetProperties.map(p => ({
        ...p,
        _highlight: problemProperties.some(pp => pp.id === p.id)
      }));
      
      setProperties(highlightedProperties);
      
      alert(`Found ${problemProperties.length} properties with coordinate issues. They are now highlighted in the list.`);
      console.log('Properties with coordinate issues:', problemProperties);
    } else {
      alert('No properties with coordinate issues found.');
    }
  };

  return (
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
        onClick={checkCoordinateIssues}
        className="text-xs text-blue-500 dark:text-blue-400 hover:underline"
      >
        Check Coordinates
      </button>
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
            includeIncomplete: true,
            noLimit: false, // Use a limit for this call as we're only looking for 1 property
            bounds: null // Make bounds parameter optional in interface
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
        pageSize: filters.limit || 1000,
        sortBy: filters.sort_by || 'created_at',
        sortAsc: filters.sort_dir === 'asc',
        includeResearch: true, // Always include research data to get better coordinates
        includeIncomplete: false, // Initially, only fetch properties with coordinates
        noLimit: true, // Bypass pagination to get all properties
        bounds: null // Make bounds parameter optional by setting to null
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
        includeIncomplete: true,
        noLimit: true // Make sure we're getting all properties
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
    // Load properties based on new bounds
    if (bounds) {
      loadPropertiesWithBounds(bounds);
    }
  };

  // Load properties with bounds
  const loadPropertiesWithBounds = async (bounds: any) => {
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
        pageSize: filters.limit || 1000,
        sortBy: filters.sort_by || 'created_at',
        sortAsc: filters.sort_dir === 'asc',
        includeResearch: true, // Always include research data to get better coordinates
        includeIncomplete: false, // Initially, only fetch properties with coordinates
        noLimit: true, // Bypass pagination to get all properties
        bounds: bounds // Apply geographic bounds
      };
      
      console.log('Fetching properties with map bounds and valid coordinates:', fetchOptions);
      
      const propertiesWithCoordinates = await fetchProperties(fetchOptions);
      
      // If we got properties with coordinates, use them
      if (propertiesWithCoordinates && propertiesWithCoordinates.length > 0) {
        console.log(`Found ${propertiesWithCoordinates.length} properties with valid coordinates in the current map view`);
        setProperties(propertiesWithCoordinates);
        setTotalProperties(propertiesWithCoordinates.length);
        setLoading(false);
        return;
      }
      
      // If no properties with coordinates were found, try without the coordinate filter
      console.log('No properties with coordinates found in current view, fetching all properties in bounds');
      
      const allFetchOptions = {
        ...fetchOptions,
        includeIncomplete: true,
        noLimit: true // Make sure we're getting all properties
      };
      
      const allProperties = await fetchProperties(allFetchOptions);
      
      if (allProperties && allProperties.length > 0) {
        console.log(`Found ${allProperties.length} total properties in bounds, but many may lack coordinates`);
        setProperties(allProperties);
        setTotalProperties(allProperties.length);
      } else {
        console.log('No properties found in the current map view');
        // Keep the existing properties instead of clearing them
        // This provides a better UX than showing an empty map
        // setProperties([]);
        // setTotalProperties(0);
      }
    } catch (err) {
      console.error('Error loading properties with bounds:', err);
      setError('Failed to load properties for the current map view. Please try again.');
    } finally {
      setLoading(false);
    }
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
        {/* Admin links for logged-in users only */}
        <AdminSidebarLinks 
          properties={properties}
          setProperties={setProperties}
        />
        
        {/* Manual geocoding control (for admins only) */}
        {selectedProperty && (
          <AdminGeocodingControl 
            selectedProperty={selectedProperty} 
            setSelectedProperty={setSelectedProperty}
            setProperties={setProperties}
          />
        )}
        
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
          <div className={`lg:w-1/3 ${showDetails ? 'hidden lg:block' : ''}`} id="property-sidebar-container">
            <PropertySidebar
              properties={properties}
              selectedProperty={selectedProperty}
              setSelectedProperty={handlePropertySelect}
              loading={loading}
            />
          </div>
          
          {/* Resizable divider */}
          <div className="hidden lg:flex flex-col items-center justify-center z-20" id="resizable-divider">
            <div className="w-3 h-full bg-transparent relative group cursor-col-resize hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors">
              {/* Main divider line - visible line running full height */}
              <div className="absolute left-1/2 top-0 bottom-0 w-0.5 bg-gray-300 dark:bg-gray-600 transform -translate-x-1/2"></div>
              
              {/* Large, obvious grip handle that resembles desktop app resizers */}
              <div className="absolute left-1/2 top-1/2 w-8 h-36 flex items-center justify-center transform -translate-x-1/2 -translate-y-1/2">
                {/* Background panel with border and shadow */}
                <div className="w-8 h-36 bg-white dark:bg-gray-800 rounded-md shadow-md border border-gray-300 dark:border-gray-600 hover:border-blue-400 dark:hover:border-blue-400 transition-all flex items-center justify-center">
                  {/* The grip dots - 2x3 grid of dots */}
                  <div className="grid grid-cols-2 gap-1.5">
                    <div className="w-1.5 h-1.5 rounded-full bg-gray-400 dark:bg-gray-500"></div>
                    <div className="w-1.5 h-1.5 rounded-full bg-gray-400 dark:bg-gray-500"></div>
                    <div className="w-1.5 h-1.5 rounded-full bg-gray-400 dark:bg-gray-500"></div>
                    <div className="w-1.5 h-1.5 rounded-full bg-gray-400 dark:bg-gray-500"></div>
                    <div className="w-1.5 h-1.5 rounded-full bg-gray-400 dark:bg-gray-500"></div>
                    <div className="w-1.5 h-1.5 rounded-full bg-gray-400 dark:bg-gray-500"></div>
                    <div className="w-1.5 h-1.5 rounded-full bg-gray-400 dark:bg-gray-500"></div>
                    <div className="w-1.5 h-1.5 rounded-full bg-gray-400 dark:bg-gray-500"></div>
                    <div className="w-1.5 h-1.5 rounded-full bg-gray-400 dark:bg-gray-500"></div>
                    <div className="w-1.5 h-1.5 rounded-full bg-gray-400 dark:bg-gray-500"></div>
                  </div>
                </div>
                
                {/* Left indicator arrow */}
                <div className="absolute -left-1 w-2 h-6 flex items-center">
                  <div className="w-0 h-0 border-t-4 border-t-transparent border-r-4 border-r-gray-400 dark:border-r-gray-500 border-b-4 border-b-transparent"></div>
                </div>
                
                {/* Right indicator arrow */}
                <div className="absolute -right-1 w-2 h-6 flex items-center">
                  <div className="w-0 h-0 border-t-4 border-t-transparent border-l-4 border-l-gray-400 dark:border-l-gray-500 border-b-4 border-b-transparent"></div>
                </div>
              </div>
            </div>
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
          <div className={`${showDetails ? 'hidden lg:block' : ''} lg:flex-1`} id="map-container">
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
      
      {/* Admin controls (already restricted to admins) */}
      <AdminControls onTriggerGeocode={handleTriggerGeocode} />
      
      {/* Add JavaScript for resizable panels */}
      <script dangerouslySetInnerHTML={{
        __html: `
          document.addEventListener('DOMContentLoaded', function() {
            const divider = document.getElementById('resizable-divider');
            const sidebarContainer = document.getElementById('property-sidebar-container');
            const mapContainer = document.getElementById('map-container');
            
            if (!divider || !sidebarContainer || !mapContainer) return;
            
            let isResizing = false;
            let startX, startWidth;
            
            // Add visual feedback elements
            const dragOverlay = document.createElement('div');
            dragOverlay.style.position = 'fixed';
            dragOverlay.style.inset = '0';
            dragOverlay.style.backgroundColor = 'transparent';
            dragOverlay.style.zIndex = '1000';
            dragOverlay.style.cursor = 'col-resize';
            dragOverlay.style.display = 'none';
            document.body.appendChild(dragOverlay);
            
            // Create attention animation for the divider
            const animateDivider = () => {
              const handle = divider.querySelector('div > div:nth-child(2)');
              if (handle) {
                // Create keyframes
                const animationStyles = document.createElement('style');
                animationStyles.textContent = `
                  @keyframes dividerAttention {
                    0% { transform: translate(-50%, -50%); }
                    25% { transform: translate(-50%, -50%) translateX(-5px); }
                    50% { transform: translate(-50%, -50%) translateX(5px); }
                    75% { transform: translate(-50%, -50%) translateX(-5px); }
                    100% { transform: translate(-50%, -50%); }
                  }
                  .divider-attention {
                    animation: dividerAttention 1.5s ease-in-out;
                  }
                `;
                document.head.appendChild(animationStyles);
                
                // Add highlight styling
                setTimeout(() => {
                  // First, add a border highlight
                  const gripPanel = handle.querySelector('div');
                  if (gripPanel) {
                    gripPanel.style.borderColor = 'rgba(59, 130, 246, 0.7)';
                    gripPanel.style.boxShadow = '0 0 10px rgba(59, 130, 246, 0.4)';
                  }
                  
                  // Then, add the animation class
                  handle.classList.add('divider-attention');
                  
                  // Reset after animation completes
                  setTimeout(() => {
                    handle.classList.remove('divider-attention');
                    if (gripPanel) {
                      gripPanel.style.borderColor = '';
                      gripPanel.style.boxShadow = '';
                    }
                  }, 1500);
                }, 1000);
              }
            };
            
            // Ensure the divider is prominent and visible
            const dividerHandle = divider.querySelector('div');
            if (dividerHandle) {
              dividerHandle.style.cursor = 'col-resize';
              dividerHandle.style.width = '8px';
              dividerHandle.style.transition = 'background-color 0.2s';
            }
            
            divider.addEventListener('mousedown', function(e) {
              // Prevent text selection during resize
              e.preventDefault();
              
              isResizing = true;
              startX = e.clientX;
              startWidth = sidebarContainer.offsetWidth;
              
              // Show overlay while dragging for smoother experience
              dragOverlay.style.display = 'block';
              
              // Add active styling to divider
              divider.classList.add('active');
              const gripPanel = divider.querySelector('div > div:nth-child(2) > div');
              if (gripPanel) {
                gripPanel.style.borderColor = 'rgba(59, 130, 246, 0.7)';
                gripPanel.style.boxShadow = '0 0 10px rgba(59, 130, 246, 0.4)';
              }
              
              document.body.classList.add('select-none');
            });
            
            document.addEventListener('mousemove', function(e) {
              if (!isResizing) return;
              
              // Get the container width dynamically to handle window resizing
              const containerWidth = document.querySelector('.container')?.offsetWidth || window.innerWidth;
              const minWidth = Math.max(200, containerWidth * 0.15); // Min 15% of container or 200px
              const maxWidth = Math.min(600, containerWidth * 0.6); // Max 60% of container or 600px
              
              // Calculate new width based on mouse movement
              let newWidth = startWidth + (e.clientX - startX);
              
              // Apply constraints
              newWidth = Math.max(minWidth, Math.min(newWidth, maxWidth));
              
              // Apply the new width with smooth transition
              sidebarContainer.style.width = newWidth + 'px';
              sidebarContainer.style.flexBasis = newWidth + 'px';
              sidebarContainer.style.flexGrow = '0';
              sidebarContainer.style.flexShrink = '0';
              
              // Update map size on drag (for better map rendering)
              if (window.requestAnimationFrame) {
                window.requestAnimationFrame(function() {
                  window.dispatchEvent(new Event('resize'));
                });
              }
            });
            
            const endResize = function() {
              if (isResizing) {
                isResizing = false;
                
                // Hide overlay
                dragOverlay.style.display = 'none';
                
                // Remove active styling from divider
                divider.classList.remove('active');
                const gripPanel = divider.querySelector('div > div:nth-child(2) > div');
                if (gripPanel) {
                  gripPanel.style.borderColor = '';
                  gripPanel.style.boxShadow = '';
                }
                
                document.body.classList.remove('select-none');
                
                // Force map to update after resize completes
                setTimeout(() => {
                  window.dispatchEvent(new Event('resize'));
                }, 100);
              }
            };
            
            document.addEventListener('mouseup', endResize);
            document.addEventListener('mouseleave', endResize);
            
            // Add touch support for mobile
            divider.addEventListener('touchstart', function(e) {
              e.preventDefault(); // Prevent scrolling while resizing
              const touch = e.touches[0];
              
              isResizing = true;
              startX = touch.clientX;
              startWidth = sidebarContainer.offsetWidth;
              
              divider.classList.add('active');
              const gripPanel = divider.querySelector('div > div:nth-child(2) > div');
              if (gripPanel) {
                gripPanel.style.borderColor = 'rgba(59, 130, 246, 0.7)';
                gripPanel.style.boxShadow = '0 0 10px rgba(59, 130, 246, 0.4)';
              }
              
              document.body.classList.add('select-none');
            });
            
            document.addEventListener('touchmove', function(e) {
              if (!isResizing) return;
              
              const touch = e.touches[0];
              const containerWidth = document.querySelector('.container')?.offsetWidth || window.innerWidth;
              const minWidth = Math.max(200, containerWidth * 0.15);
              const maxWidth = Math.min(600, containerWidth * 0.6);
              
              let newWidth = startWidth + (touch.clientX - startX);
              newWidth = Math.max(minWidth, Math.min(newWidth, maxWidth));
              
              sidebarContainer.style.width = newWidth + 'px';
              sidebarContainer.style.flexBasis = newWidth + 'px';
              sidebarContainer.style.flexGrow = '0';
              sidebarContainer.style.flexShrink = '0';
              
              // Update map during touch drag
              if (window.requestAnimationFrame) {
                window.requestAnimationFrame(function() {
                  window.dispatchEvent(new Event('resize'));
                });
              }
            });
            
            document.addEventListener('touchend', endResize);
            document.addEventListener('touchcancel', endResize);
            
            // Save the sidebar width in localStorage to persist between sessions
            window.addEventListener('beforeunload', function() {
              if (sidebarContainer.style.width) {
                localStorage.setItem('propertySidebarWidth', sidebarContainer.style.width);
              }
            });
            
            // Restore saved width on page load
            const savedWidth = localStorage.getItem('propertySidebarWidth');
            if (savedWidth) {
              sidebarContainer.style.width = savedWidth;
              sidebarContainer.style.flexBasis = savedWidth;
              sidebarContainer.style.flexGrow = '0';
              sidebarContainer.style.flexShrink = '0';
            }

            // Run the animation to draw attention to the divider
            setTimeout(animateDivider, 2000);
            
            // Add a tooltip to explain the divider functionality
            const tooltip = document.createElement('div');
            tooltip.style.position = 'absolute';
            tooltip.style.top = '50%';
            tooltip.style.left = '100%';
            tooltip.style.transform = 'translateY(-50%)';
            tooltip.style.marginLeft = '10px';
            tooltip.style.padding = '5px 10px';
            tooltip.style.backgroundColor = 'rgba(0, 0, 0, 0.8)';
            tooltip.style.color = 'white';
            tooltip.style.borderRadius = '4px';
            tooltip.style.fontSize = '12px';
            tooltip.style.whiteSpace = 'nowrap';
            tooltip.style.pointerEvents = 'none';
            tooltip.style.opacity = '0';
            tooltip.style.transition = 'opacity 0.3s ease';
            tooltip.style.zIndex = '1000';
            tooltip.textContent = 'Drag to resize';
            
            divider.appendChild(tooltip);
            
            divider.addEventListener('mouseenter', function() {
              tooltip.style.opacity = '1';
            });
            
            divider.addEventListener('mouseleave', function() {
              tooltip.style.opacity = '0';
            });
          });
        `
      }} />
    </Layout>
  );
};

// New component for admin geocoding control
const AdminGeocodingControl = ({ selectedProperty, setSelectedProperty, setProperties }) => {
  const [isAdmin, setIsAdmin] = useState(false);

  useEffect(() => {
    // Check if the user is logged in
    const checkAdmin = async () => {
      const { data: { session } } = await supabase.auth.getSession();
      setIsAdmin(!!session);
    };
    
    checkAdmin();
  }, []);

  if (!isAdmin || !selectedProperty) return null;

  return (
    <div className="absolute top-4 left-56 z-10">
      <button
        onClick={() => {
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
        className="px-3 py-1 text-xs bg-purple-500 text-white rounded hover:bg-purple-600"
      >
        Geocode Selected Property
      </button>
    </div>
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