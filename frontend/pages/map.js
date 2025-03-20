import React, { useState, useEffect } from 'react';
import dynamic from 'next/dynamic';
import Layout from '../src/components/Layout';
import { fetchProperties } from '../lib/supabase';

// Import the map component dynamically to avoid SSR issues with Leaflet
const MapComponent = dynamic(
  () => import('../src/components/MapComponent'),
  { ssr: false }
);

export default function MapPage() {
  const [properties, setProperties] = useState([]);
  const [selectedProperty, setSelectedProperty] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadProperties() {
      try {
        setLoading(true);
        const data = await fetchProperties({ 
          sortBy: 'created_at', 
          sortAsc: false,
          page: 1,
          pageSize: 100,
          filters: {},
          includeIncomplete: true,
          includeResearch: true
        });
        console.log(`Loaded ${data.length} properties for map`);
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
    <Layout title="Property Map | Austin Multifamily">
      <div className="container mx-auto px-4">
        <h1 className="text-2xl font-bold mb-4">Property Map {loading ? '(Loading...)' : `(${properties.length} properties)`}</h1>
        <div className="h-[80vh]">
          <MapComponent 
            properties={properties} 
            selectedProperty={selectedProperty}
            setSelectedProperty={setSelectedProperty}
          />
        </div>
      </div>
    </Layout>
  );
} 