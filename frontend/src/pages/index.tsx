import { useEffect, useState } from 'react';
import Head from 'next/head';
import Link from 'next/link';
import { useSupabaseClient } from '@supabase/auth-helpers-react';

export default function Home() {
  const [properties, setProperties] = useState([]);
  const [loading, setLoading] = useState(true);
  const supabase = useSupabaseClient();

  useEffect(() => {
    async function fetchProperties() {
      try {
        setLoading(true);
        // Fetch properties from Supabase
        const { data, error } = await supabase
          .from('properties')
          .select('*')
          .limit(10);

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
        <title>Austin Multifamily Property Listing Map</title>
        <meta name="description" content="Comprehensive map of multifamily property listings in Austin, Texas" />
        <link rel="icon" href="/favicon.ico" />
      </Head>

      <header className="bg-white shadow">
        <div className="max-w-7xl mx-auto py-6 px-4 sm:px-6 lg:px-8">
          <h1 className="text-3xl font-bold text-gray-900">
            Austin Multifamily Property Listing Map
          </h1>
        </div>
      </header>

      <main className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        <div className="px-4 py-6 sm:px-0">
          <div className="border-4 border-dashed border-gray-200 rounded-lg p-4 min-h-[70vh]">
            {loading ? (
              <p className="text-center text-gray-500">Loading properties...</p>
            ) : properties.length > 0 ? (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {properties.map((property: any) => (
                  <div key={property.id} className="bg-white p-4 rounded shadow">
                    <h2 className="text-xl font-semibold">{property.name}</h2>
                    <p className="text-gray-600">{property.address}</p>
                    <p className="text-gray-600">Units: {property.num_units}</p>
                    {property.year_built && (
                      <p className="text-gray-600">Built: {property.year_built}</p>
                    )}
                    <p className="text-gray-600 mt-2">
                      Status: <span className="font-medium">{property.status}</span>
                    </p>
                    <div className="mt-4">
                      <Link href={`/properties/${property.id}`} className="text-blue-600 hover:text-blue-800">
                        View Details
                      </Link>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center">
                <p className="text-gray-500">No properties found.</p>
                <p className="mt-2">
                  Check back soon as we aggregate listings from across Austin.
                </p>
              </div>
            )}
            
            <div className="mt-8 text-center">
              <Link href="/map" className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700">
                View Interactive Map
              </Link>
            </div>
          </div>
        </div>
      </main>

      <footer className="bg-white">
        <div className="max-w-7xl mx-auto py-6 px-4 overflow-hidden sm:px-6 lg:px-8">
          <p className="text-center text-gray-500">
            &copy; {new Date().getFullYear()} Austin Multifamily Property Listing Map
          </p>
        </div>
      </footer>
    </div>
  );
} 