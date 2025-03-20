import React, { useEffect, useState } from 'react';
import { useRouter } from 'next/router';
import Layout from '../components/Layout';
import { useAuth } from '../contexts/AuthContext';
import { supabase } from '../../lib/supabase';

interface SavedSearch {
  id: string;
  name: string;
  filters: Record<string, any>;
  created_at: string;
}

interface SavedProperty {
  id: string;
  property_id: string;
  property_name: string;
  address: string;
  created_at: string;
}

const Dashboard: React.FC = () => {
  const { user, loading } = useAuth();
  const router = useRouter();
  const [savedSearches, setSavedSearches] = useState<SavedSearch[]>([]);
  const [savedProperties, setSavedProperties] = useState<SavedProperty[]>([]);
  const [activeTab, setActiveTab] = useState('searches');
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    // Redirect if not logged in
    if (!loading && !user) {
      router.push('/login');
    }
  }, [user, loading, router]);

  useEffect(() => {
    if (user) {
      // Fetch user's saved searches and properties
      const fetchUserData = async () => {
        try {
          setIsLoading(true);

          // In a real implementation, these would be actual tables in your Supabase database
          // For now, we'll use mock data
          const mockSearches = [
            {
              id: '1',
              name: 'Downtown Properties',
              filters: { neighborhood: 'downtown', min_units: 50 },
              created_at: '2023-01-15T12:00:00Z',
            },
            {
              id: '2',
              name: 'North Austin Under $10M',
              filters: { area: 'north', max_price: 10000000 },
              created_at: '2023-02-20T15:30:00Z',
            },
          ];

          const mockProperties = [
            {
              id: '1',
              property_id: 'prop123',
              property_name: 'The Monarch',
              address: '801 W 5th St, Austin, TX 78703',
              created_at: '2023-03-05T09:15:00Z',
            },
            {
              id: '2',
              property_id: 'prop456',
              property_name: 'Gables Park Plaza',
              address: '115 Sandra Muraida Way, Austin, TX 78703',
              created_at: '2023-03-10T14:20:00Z',
            },
          ];

          // In a real implementation, you'd fetch from Supabase like this:
          // const { data: searchesData } = await supabase
          //   .from('saved_searches')
          //   .select('*')
          //   .eq('user_id', user.id);
          
          // const { data: propertiesData } = await supabase
          //   .from('saved_properties')
          //   .select('*, properties(*)')
          //   .eq('user_id', user.id);

          setSavedSearches(mockSearches);
          setSavedProperties(mockProperties);
        } catch (error) {
          console.error('Error fetching user data:', error);
        } finally {
          setIsLoading(false);
        }
      };

      fetchUserData();
    }
  }, [user]);

  if (loading || !user) {
    return (
      <Layout title="Dashboard | Austin Multifamily Map">
        <div className="flex items-center justify-center min-h-[calc(100vh-200px)]">
          <div className="text-center">Loading...</div>
        </div>
      </Layout>
    );
  }

  return (
    <Layout title="Dashboard | Austin Multifamily Map">
      <div className="container mx-auto px-4 py-8">
        <div className="max-w-6xl mx-auto">
          <div className="flex flex-col md:flex-row md:items-center md:justify-between mb-8">
            <div>
              <h1 className="text-3xl font-bold text-gray-800">Dashboard</h1>
              <p className="text-gray-600 mt-1">Welcome back, {user.email}</p>
            </div>
            <div className="mt-4 md:mt-0">
              <button 
                className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700 transition"
                onClick={() => router.push('/map')}
              >
                Browse Map
              </button>
            </div>
          </div>

          <div className="bg-white shadow-md rounded-lg overflow-hidden">
            <div className="border-b">
              <div className="flex">
                <button
                  className={`px-6 py-3 text-sm font-medium ${
                    activeTab === 'searches'
                      ? 'text-blue-600 border-b-2 border-blue-600'
                      : 'text-gray-500 hover:text-gray-700'
                  }`}
                  onClick={() => setActiveTab('searches')}
                >
                  Saved Searches
                </button>
                <button
                  className={`px-6 py-3 text-sm font-medium ${
                    activeTab === 'properties'
                      ? 'text-blue-600 border-b-2 border-blue-600'
                      : 'text-gray-500 hover:text-gray-700'
                  }`}
                  onClick={() => setActiveTab('properties')}
                >
                  Saved Properties
                </button>
              </div>
            </div>

            <div className="p-6">
              {isLoading ? (
                <div className="text-center py-12">
                  <p>Loading...</p>
                </div>
              ) : activeTab === 'searches' ? (
                <div>
                  <h2 className="text-xl font-semibold text-gray-800 mb-4">Your Saved Searches</h2>
                  
                  {savedSearches.length === 0 ? (
                    <div className="text-center py-8 text-gray-500">
                      <p>You don't have any saved searches yet.</p>
                      <button 
                        className="mt-4 text-blue-600 hover:underline"
                        onClick={() => router.push('/map')}
                      >
                        Create your first search
                      </button>
                    </div>
                  ) : (
                    <div className="overflow-x-auto">
                      <table className="min-w-full divide-y divide-gray-200">
                        <thead className="bg-gray-50">
                          <tr>
                            <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                              Name
                            </th>
                            <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                              Filters
                            </th>
                            <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                              Created
                            </th>
                            <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                              Actions
                            </th>
                          </tr>
                        </thead>
                        <tbody className="bg-white divide-y divide-gray-200">
                          {savedSearches.map((search) => (
                            <tr key={search.id}>
                              <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                                {search.name}
                              </td>
                              <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                {Object.entries(search.filters).map(([key, value]) => (
                                  <span key={key} className="inline-block bg-gray-100 rounded-full px-3 py-1 text-xs font-semibold text-gray-700 mr-2 mb-2">
                                    {key}: {value}
                                  </span>
                                ))}
                              </td>
                              <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                {new Date(search.created_at).toLocaleDateString()}
                              </td>
                              <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                                <button className="text-blue-600 hover:text-blue-900 mr-4">View</button>
                                <button className="text-red-600 hover:text-red-900">Delete</button>
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  )}
                </div>
              ) : (
                <div>
                  <h2 className="text-xl font-semibold text-gray-800 mb-4">Your Saved Properties</h2>
                  
                  {savedProperties.length === 0 ? (
                    <div className="text-center py-8 text-gray-500">
                      <p>You don't have any saved properties yet.</p>
                      <button 
                        className="mt-4 text-blue-600 hover:underline"
                        onClick={() => router.push('/map')}
                      >
                        Browse properties
                      </button>
                    </div>
                  ) : (
                    <div className="overflow-x-auto">
                      <table className="min-w-full divide-y divide-gray-200">
                        <thead className="bg-gray-50">
                          <tr>
                            <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                              Property
                            </th>
                            <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                              Address
                            </th>
                            <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                              Saved On
                            </th>
                            <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                              Actions
                            </th>
                          </tr>
                        </thead>
                        <tbody className="bg-white divide-y divide-gray-200">
                          {savedProperties.map((property) => (
                            <tr key={property.id}>
                              <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                                {property.property_name}
                              </td>
                              <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                {property.address}
                              </td>
                              <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                {new Date(property.created_at).toLocaleDateString()}
                              </td>
                              <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                                <button className="text-blue-600 hover:text-blue-900 mr-4">View</button>
                                <button className="text-red-600 hover:text-red-900">Remove</button>
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </Layout>
  );
};

export default Dashboard;