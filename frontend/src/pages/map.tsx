import { useEffect, useState } from 'react';
import Head from 'next/head';
import dynamic from 'next/dynamic';
import { useSupabaseClient } from '@supabase/auth-helpers-react';
import PropertySidebar from '../components/PropertySidebar';
import PropertyDetails from '../components/PropertyDetails';
import { Property, PropertySearchParams } from '../types/property';

// Import the map component dynamically to avoid SSR issues with Leaflet
const MapComponent = dynamic(() => import('../components/MapComponent'), {
  ssr: false,
  loading: () => (
    <div className="h-[80vh] lg:h-[85vh] bg-gray-200 rounded-lg flex items-center justify-center">
      <div className="text-center">
        <svg
          className="animate-spin h-8 w-8 text-gray-500 mx-auto mb-2"
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
        <p>Loading map...</p>
      </div>
    </div>
  )
});

export default function MapPage() {
  // State
  const [properties, setProperties] = useState<Property[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedProperty, setSelectedProperty] = useState<Property | null>(null);
  const [showDetails, setShowDetails] = useState(false);
  const [searchParams, setSearchParams] = useState<PropertySearchParams>({
    page: 1,
    limit: 100
  });
  
  // Get Supabase client
  const supabase = useSupabaseClient();
  
  // Get Mapbox token from environment
  const mapboxToken = process.env.NEXT_PUBLIC_MAPBOX_ACCESS_TOKEN;

  // Fetch properties
  useEffect(() => {
    async function fetchProperties() {
      try {
        setLoading(true);
        
        // Build query
        let query = supabase.from('properties').select('*');
        
        // Apply filters
        if (searchParams.status && searchParams.status !== 'all') {
          query = query.ilike('status', `%${searchParams.status}%`);
        }
        
        if (searchParams.min_price) {
          query = query.gte('price', searchParams.min_price);
        }
        
        if (searchParams.max_price) {
          query = query.lte('price', searchParams.max_price);
        }
        
        if (searchParams.min_units) {
          // Check both units and num_units columns
          query = query.or(`units.gte.${searchParams.min_units},num_units.gte.${searchParams.min_units}`);
        }
        
        if (searchParams.max_units) {
          // Check both units and num_units columns
          query = query.or(`units.lte.${searchParams.max_units},num_units.lte.${searchParams.max_units}`);
        }
        
        if (searchParams.city) {
          query = query.ilike('city', `%${searchParams.city}%`);
        }
        
        if (searchParams.state) {
          query = query.ilike('state', searchParams.state);
        }
        
        // Apply pagination
        if (searchParams.page && searchParams.limit) {
          const start = (searchParams.page - 1) * searchParams.limit;
          const end = start + searchParams.limit - 1;
          query = query.range(start, end);
        }
        
        // Execute query
        const { data, error } = await query;

        if (error) {
          throw error;
        }

        if (data) {
          setProperties(data as Property[]);
        }
      } catch (error) {
        console.error('Error fetching properties:', error);
      } finally {
        setLoading(false);
      }
    }

    fetchProperties();
  }, [supabase, searchParams]);
  
  // Handle property selection
  const handlePropertySelect = (property: Property | null) => {
    setSelectedProperty(property);
    if (property) {
      setShowDetails(true);
    }
  };
  
  // Handle map bounds change
  const handleBoundsChange = (bounds: any) => {
    // Update search params with map bounds
    setSearchParams(prev => ({
      ...prev,
      bounds
    }));
  };

  return (
    <div className="min-h-screen bg-gray-100">
      <Head>
        <title>Interactive Map | Austin Multifamily Property Listing Map</title>
        <meta name="description" content="Interactive map of multifamily property listings in Austin, Texas" />
        <link rel="icon" href="/favicon.ico" />
      </Head>

      <header className="bg-white shadow">
        <div className="max-w-7xl mx-auto py-4 px-4 sm:px-6 lg:px-8 flex justify-between items-center">
          <h1 className="text-2xl font-bold text-gray-900">
            Austin Multifamily Property Map
          </h1>
          <div className="flex space-x-4 items-center">
            <a href="/" className="text-blue-600 hover:text-blue-800">
              Home
            </a>
            <button className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg transition">
              Sign In
            </button>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        <div className="px-4 py-2 sm:px-0">
          <div className="flex flex-col lg:flex-row gap-4">
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
                  onClose={() => setShowDetails(false)}
                />
              </div>
            )}
            
            {/* Map container */}
            <div className={`${showDetails ? 'hidden lg:block' : ''} lg:flex-1`}>
              <MapComponent 
                properties={properties} 
                selectedProperty={selectedProperty}
                setSelectedProperty={handlePropertySelect}
                onBoundsChange={handleBoundsChange}
                mapboxToken={mapboxToken}
              />
            </div>
            
            {/* Property details panel (desktop: third column) */}
            {showDetails && (
              <div className="hidden lg:block lg:w-1/3">
                <PropertyDetails
                  property={selectedProperty!}
                  onClose={() => setShowDetails(false)}
                />
              </div>
            )}
          </div>
        </div>
      </main>

      <footer className="bg-white mt-8">
        <div className="max-w-7xl mx-auto py-4 px-4 overflow-hidden sm:px-6 lg:px-8">
          <p className="text-center text-gray-500">
            &copy; {new Date().getFullYear()} Austin Multifamily Property Listing Map
          </p>
        </div>
      </footer>
    </div>
  );
}