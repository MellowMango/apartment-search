import { useState, useEffect } from 'react';
import { useRouter } from 'next/router';
import Layout from '../../components/Layout';
import { checkResearchTableExists, syncResearchCoordinates } from '../../../lib/geocoding';
import { supabase } from '../../../lib/supabase';

// Admin dashboard for synchronizing coordinates
export default function SyncCoordinatesPage() {
  const [isLoading, setIsLoading] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [hasResearchTable, setHasResearchTable] = useState<boolean | null>(null);
  const [limit, setLimit] = useState(100);
  const router = useRouter();
  
  // Check if user is authenticated and has admin role
  useEffect(() => {
    const checkAuth = async () => {
      const { data: { user } } = await supabase.auth.getUser();
      
      if (!user) {
        router.push('/login?redirect=/admin/sync-coordinates');
        return;
      }
      
      // Check if research table exists
      const tableExists = await checkResearchTableExists();
      setHasResearchTable(tableExists);
    };
    
    checkAuth();
  }, [router]);
  
  // Handle the sync process
  const handleSync = async () => {
    setIsLoading(true);
    try {
      const syncResult = await syncResearchCoordinates(limit);
      setResult(syncResult);
    } catch (error) {
      console.error('Error synchronizing coordinates:', error);
      setResult({
        success: false,
        message: error.message || 'An error occurred',
        updated: 0,
        errors: 0
      });
    } finally {
      setIsLoading(false);
    }
  };
  
  return (
    <Layout title="Sync Property Coordinates | Admin">
      <div className="container mx-auto px-4 py-8">
        <div className="max-w-3xl mx-auto">
          <h1 className="text-3xl font-bold mb-6">Synchronize Property Coordinates</h1>
          
          <div className="bg-white dark:bg-gray-800 shadow-md rounded-lg p-6 mb-8">
            <h2 className="text-xl font-semibold mb-4">About This Tool</h2>
            <p className="text-gray-700 dark:text-gray-300 mb-4">
              This tool synchronizes property coordinates from the research data to the properties table.
              It will update properties that have missing or grid-pattern coordinates with valid coordinates
              from the property research data.
            </p>
            
            {hasResearchTable === false && (
              <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
                <p className="font-bold">Research Table Missing</p>
                <p>The property_research table doesn't exist or isn't accessible. Synchronization cannot be performed.</p>
              </div>
            )}
            
            {hasResearchTable === true && (
              <div className="bg-green-100 border border-green-400 text-green-700 px-4 py-3 rounded mb-4">
                <p className="font-bold">Research Table Available</p>
                <p>The property_research table is available. You can proceed with synchronization.</p>
              </div>
            )}
            
            <div className="mt-6">
              <label className="block text-gray-700 dark:text-gray-300 mb-2">
                Maximum properties to process:
                <input
                  type="number"
                  value={limit}
                  onChange={(e) => setLimit(parseInt(e.target.value) || 100)}
                  min="1"
                  max="1000"
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 dark:bg-gray-700 dark:border-gray-600 dark:text-white"
                />
              </label>
              
              <button
                onClick={handleSync}
                disabled={isLoading || hasResearchTable === false}
                className={`mt-4 py-2 px-4 rounded font-bold ${
                  isLoading || hasResearchTable === false
                    ? 'bg-gray-400 cursor-not-allowed'
                    : 'bg-blue-600 hover:bg-blue-700 text-white'
                }`}
              >
                {isLoading ? 'Synchronizing...' : 'Synchronize Coordinates'}
              </button>
            </div>
          </div>
          
          {result && (
            <div className={`bg-white dark:bg-gray-800 shadow-md rounded-lg p-6 ${
              result.success ? 'border-green-500' : 'border-red-500'
            } border-l-4`}>
              <h2 className="text-xl font-semibold mb-4">Synchronization Results</h2>
              
              <div className="mb-4">
                <p className={`text-lg font-medium ${
                  result.success ? 'text-green-600' : 'text-red-600'
                }`}>
                  {result.success ? 'Synchronization Completed' : 'Synchronization Failed'}
                </p>
                <p className="text-gray-700 dark:text-gray-300 mt-2">{result.message}</p>
              </div>
              
              {result.success && (
                <div className="grid grid-cols-2 gap-4 mt-4">
                  <div className="bg-gray-100 dark:bg-gray-700 p-4 rounded">
                    <p className="text-lg font-semibold text-green-600">{result.updated}</p>
                    <p className="text-gray-700 dark:text-gray-300">Properties Updated</p>
                  </div>
                  <div className="bg-gray-100 dark:bg-gray-700 p-4 rounded">
                    <p className="text-lg font-semibold text-red-600">{result.errors}</p>
                    <p className="text-gray-700 dark:text-gray-300">Errors</p>
                  </div>
                </div>
              )}
              
              <div className="mt-6">
                <button
                  onClick={() => router.push('/map')}
                  className="py-2 px-4 bg-gray-600 hover:bg-gray-700 text-white rounded font-bold mr-2"
                >
                  View Map
                </button>
                
                <button
                  onClick={() => setResult(null)}
                  className="py-2 px-4 bg-gray-200 hover:bg-gray-300 text-gray-800 rounded font-bold"
                >
                  Clear Results
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </Layout>
  );
}