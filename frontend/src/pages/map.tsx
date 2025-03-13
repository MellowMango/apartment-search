import { useEffect, useState } from 'react';
import Head from 'next/head';
import dynamic from 'next/dynamic';
import { useSupabaseClient } from '@supabase/auth-helpers-react';

// Import the map component dynamically to avoid SSR issues with Leaflet
const MapComponent = dynamic(() => import('../components/MapComponent'), {
  ssr: false,
  loading: () => <div className="h-[70vh] bg-gray-200 flex items-center justify-center">Loading map...</div>
});

export default function MapPage() {
  const [properties, setProperties] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedProperty, setSelectedProperty] = useState(null);
  const supabase = useSupabaseClient();

  useEffect(() => {
    async function fetchProperties() {
      try {
        setLoading(true);
        // Fetch properties from Supabase
        const { data, error } = await supabase
          .from('properties')
          .select('*');

        if (error) {
          throw error;
        }

        if (data) {
          setProperties(data);
        }
      } catch (error) {
        console.error('Error fetching properties:', error);
      } finally {
        setLoading(false);
      }
    }

    fetchProperties();
  }, [supabase]);

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
            Interactive Property Map
          </h1>
          <a href="/" className="text-blue-600 hover:text-blue-800">
            Back to Home
          </a>
        </div>
      </header>

      <main className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        <div className="px-4 py-6 sm:px-0">
          <div className="flex flex-col lg:flex-row gap-4">
            {/* Property sidebar */}
            <div className="lg:w-1/3 bg-white p-4 rounded shadow overflow-y-auto max-h-[70vh]">
              <h2 className="text-xl font-semibold mb-4">Properties</h2>
              
              {loading ? (
                <p className="text-center text-gray-500">Loading properties...</p>
              ) : properties.length > 0 ? (
                <div className="space-y-4">
                  {properties.map((property: any) => (
                    <div 
                      key={property.id} 
                      className={`p-3 rounded cursor-pointer transition ${
                        selectedProperty?.id === property.id 
                          ? 'bg-blue-100 border-l-4 border-blue-500' 
                          : 'bg-gray-50 hover:bg-gray-100'
                      }`}
                      onClick={() => setSelectedProperty(property)}
                    >
                      <h3 className="font-medium">{property.name}</h3>
                      <p className="text-sm text-gray-600">{property.address}</p>
                      <div className="flex justify-between mt-2 text-sm">
                        <span>{property.num_units} units</span>
                        <span className={`px-2 py-1 rounded-full text-xs ${
                          property.status === 'Actively Marketed' 
                            ? 'bg-green-100 text-green-800' 
                            : property.status === 'Under Contract' 
                            ? 'bg-yellow-100 text-yellow-800' 
                            : 'bg-red-100 text-red-800'
                        }`}>
                          {property.status}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-center text-gray-500">No properties found.</p>
              )}
            </div>
            
            {/* Map container */}
            <div className="lg:w-2/3">
              <MapComponent 
                properties={properties} 
                selectedProperty={selectedProperty}
                setSelectedProperty={setSelectedProperty}
              />
            </div>
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