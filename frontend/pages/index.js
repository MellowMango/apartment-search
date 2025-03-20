import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import Layout from '../src/components/Layout';
import { fetchProperties } from '../lib/supabase';

export default function HomePage() {
  const [properties, setProperties] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadProperties() {
      try {
        setLoading(true);
        // Fetch properties using our utility function - include those with missing coordinates
        const data = await fetchProperties({ 
          sortBy: 'created_at', 
          sortAsc: false,
          pageSize: 9,
          page: 1,
          filters: {},
          includeIncomplete: true, // Show properties even if they have missing coordinates
          includeResearch: true
        });
        
        console.log(`Loaded ${data.length} properties for homepage`);
        setProperties(data);
      } catch (error) {
        console.error('Error fetching properties:', error);
      } finally {
        setLoading(false);
      }
    }

    loadProperties();
  }, []);

  return (
    <Layout title="Austin Multifamily Property Listing Map">
      {/* Hero Section */}
      <section className="relative bg-blue-700 text-white">
        <div className="absolute inset-0 bg-gradient-to-r from-blue-800 to-blue-600 opacity-90"></div>
        <div className="relative max-w-7xl mx-auto px-4 py-24 sm:px-6 lg:px-8 flex flex-col items-center">
          <h1 className="text-4xl md:text-5xl font-extrabold tracking-tight text-center mb-6">
            Austin Multifamily <br className="hidden sm:block" />Property Listings
          </h1>
          <p className="text-xl text-center max-w-3xl mb-10">
            Discover and analyze multifamily properties across Austin with our interactive map and comprehensive data.
          </p>
          <div className="flex flex-col sm:flex-row space-y-4 sm:space-y-0 sm:space-x-4">
            <Link href="/map" className="inline-flex items-center justify-center px-6 py-3 border border-transparent text-base font-medium rounded-md text-blue-700 bg-white hover:bg-gray-100 shadow-lg">
              Explore the Map
            </Link>
            <Link href="/signup" className="inline-flex items-center justify-center px-6 py-3 border border-white text-base font-medium rounded-md text-white hover:bg-blue-800 hover:border-transparent">
              Create Account
            </Link>
          </div>
        </div>
      </section>
    </Layout>
  );
} 