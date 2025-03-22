import { useState, useEffect } from 'react';
import { useRouter } from 'next/router';
import { supabase } from '../../../lib/supabase';
import Layout from '../../components/Layout';
import { triggerBatchGeocode, getGeocodingStats, checkGeocodingTaskStatus, verifyCoordinates, getVerificationTaskResults } from '../../utils/geocodingApi';

// TaskItem component for displaying task status
const TaskItem = ({ taskId, onRefresh }) => {
  const [taskStatus, setTaskStatus] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  
  const fetchTaskStatus = async () => {
    try {
      setIsLoading(true);
      setError(null);
      
      // First get basic task info to determine the type
      const basicTaskInfo = await checkGeocodingTaskStatus(taskId);
      
      // Get detailed task status with the appropriate function based on task type
      let taskData;
      if (basicTaskInfo.task_type === 'verify_coordinates') {
        taskData = await getVerificationTaskResults(taskId);
      } else {
        taskData = basicTaskInfo;
      }
      
      setTaskStatus(taskData);
    } catch (error) {
      console.error('Error fetching task status:', error);
      setError(error.message || 'Failed to fetch task status');
    } finally {
      setIsLoading(false);
    }
  };
  
  useEffect(() => {
    fetchTaskStatus();
  }, [taskId]);
  
  return (
    <div className="border rounded p-4 mb-4">
      <div className="flex justify-between items-center mb-2">
        <h3 className="font-semibold truncate">Task: {taskId}</h3>
        <button
          className="text-sm text-blue-600 hover:text-blue-800"
          onClick={() => {
            fetchTaskStatus();
            if (onRefresh) onRefresh();
          }}
          disabled={isLoading}
        >
          {isLoading ? 'Refreshing...' : 'Refresh'}
        </button>
      </div>
      
      {isLoading && !taskStatus ? (
        <div className="text-gray-500 text-sm">Loading task status...</div>
      ) : error ? (
        <div className="text-red-500 text-sm">{error}</div>
      ) : taskStatus ? (
        <div>
          <div className="grid grid-cols-2 gap-2 text-sm mb-3">
            <div>
              <span className="text-gray-500">Status:</span>{' '}
              <span className={`font-medium ${taskStatus.status === 'completed' ? 'text-green-600' : taskStatus.status === 'error' ? 'text-red-600' : 'text-blue-600'}`}>
                {taskStatus.status}
              </span>
            </div>
            <div>
              <span className="text-gray-500">Type:</span>{' '}
              <span className="font-medium">
                {taskStatus.task_type === 'verify_coordinates' 
                  ? 'Coordinate Verification' 
                  : 'Batch Geocoding'}
              </span>
            </div>
            {taskStatus.start_time && (
              <div>
                <span className="text-gray-500">Started:</span>{' '}
                {new Date(taskStatus.start_time).toLocaleString()}
              </div>
            )}
            {taskStatus.end_time && (
              <div>
                <span className="text-gray-500">Completed:</span>{' '}
                {new Date(taskStatus.end_time).toLocaleString()}
              </div>
            )}
            {taskStatus.duration_seconds !== undefined && (
              <div>
                <span className="text-gray-500">Duration:</span>{' '}
                {taskStatus.duration_seconds.toFixed(1)}s
              </div>
            )}
          </div>
          
          {taskStatus.status === 'completed' && (
            <div className="mt-2">
              <h4 className="font-semibold">Results:</h4>
              {taskStatus.task_type === 'verify_coordinates' ? (
                <div>
                  <p>
                    Processed: <span className="font-medium">{taskStatus.properties_processed || 0}</span> properties
                  </p>
                  <p>
                    Success rate: <span className="font-medium">{Math.round(taskStatus.success_rate || 0)}%</span>
                  </p>
                  {taskStatus.verificationStats && (
                    <div className="mt-1 text-sm">
                      <p className="font-medium">Distance from Google Maps coordinates:</p>
                      <ul className="ml-4 list-disc">
                        <li>Very accurate (under 10m): {taskStatus.verificationStats.distanceRanges.accurate}</li>
                        <li>Minor difference (10-100m): {taskStatus.verificationStats.distanceRanges.minor}</li>
                        <li>Major difference (100-1000m): {taskStatus.verificationStats.distanceRanges.major}</li>
                        <li>Extreme difference (over 1km): {taskStatus.verificationStats.distanceRanges.extreme}</li>
                        <li>Failed to verify: {taskStatus.verificationStats.distanceRanges.errors}</li>
                      </ul>
                      <p className="mt-1">
                        <span className="font-medium">{taskStatus.verificationStats.updatedCount}</span> properties had coordinates updated
                      </p>
                    </div>
                  )}
                </div>
              ) : (
                <p>
                  Success: <span className="font-medium">{taskStatus.success_count || 0}</span>,
                  Errors: <span className="font-medium">{taskStatus.error_count || 0}</span>,
                  Success rate: <span className="font-medium">{Math.round(taskStatus.success_rate || 0)}%</span>
                </p>
              )}
            </div>
          )}
          
          {taskStatus.error_message && (
            <div className="mt-2 text-red-600 text-sm">
              <div className="font-medium">Error:</div>
              <div>{taskStatus.error_message}</div>
            </div>
          )}
        </div>
      ) : (
        <div className="text-gray-500 text-sm">No task data available</div>
      )}
    </div>
  );
};

export default function GeocodingAdmin() {
  const router = useRouter();
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [batchSize, setBatchSize] = useState(100);
  const [recentTasks, setRecentTasks] = useState([]);
  const [isAdmin, setIsAdmin] = useState(false);
  const [forceRefresh, setForceRefresh] = useState(false);
  const [coordinateVerificationBatchSize, setCoordinateVerificationBatchSize] = useState(50);
  const [coordinateVerificationCheckAll, setCoordinateVerificationCheckAll] = useState(false);
  const [coordinateVerificationCheckSuspicious, setCoordinateVerificationCheckSuspicious] = useState(true);
  const [coordinateVerificationAutoFix, setCoordinateVerificationAutoFix] = useState(true);
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    const checkAuth = async () => {
      const { data: { session } } = await supabase.auth.getSession();
      if (!session) {
        router.push('/login');
        return;
      }
      setIsAdmin(true);
      loadStats();
    };
    
    checkAuth();
  }, [router]);

  const loadStats = async () => {
    try {
      setLoading(true);
      const geocodingStats = await getGeocodingStats();
      setStats(geocodingStats);
    } catch (err) {
      console.error('Failed to load geocoding stats:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleStartGeocodingTask = async () => {
    try {
      setLoading(true);
      const result = await triggerBatchGeocode(batchSize, forceRefresh);
      
      // Add the new task to the list of recent tasks
      setRecentTasks(prev => [result.task_id, ...prev.slice(0, 4)]);
      loadStats();
    } catch (err) {
      console.error('Failed to start geocoding task:', err);
      alert('Failed to start geocoding task: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  /**
   * Handle starting a coordinate verification task
   */
  const handleVerifyCoordinates = async () => {
    try {
      setIsLoading(true);
      
      const confirmed = window.confirm(
        `Are you sure you want to verify coordinates for ${coordinateVerificationBatchSize} properties? ${
          coordinateVerificationAutoFix ? 'Incorrect coordinates will be automatically fixed.' : 'Coordinates will be checked but not modified.'
        }`
      );
      
      if (!confirmed) {
        setIsLoading(false);
        return;
      }
      
      const taskId = await verifyCoordinates({
        batchSize: coordinateVerificationBatchSize,
        checkAll: coordinateVerificationCheckAll,
        autoFix: coordinateVerificationAutoFix
      });
      
      // Add task to the list
      setRecentTasks(prev => [taskId, ...prev].slice(0, 10));
      
      alert(`Coordinate verification task started with ID: ${taskId}`);
      
      // Refresh stats after a short delay
      setTimeout(() => {
        loadStats();
      }, 2000);
    } catch (error) {
      console.error('Error starting coordinate verification:', error);
      alert(`Error: ${error.message}`);
    } finally {
      setIsLoading(false);
    }
  };

  if (!isAdmin) {
    return (
      <Layout>
        <div className="container mx-auto px-4 py-8">
          <div className="text-center py-12">Checking authentication...</div>
        </div>
      </Layout>
    );
  }

  return (
    <Layout>
      <div className="container mx-auto px-4 py-8">
        <h1 className="text-3xl font-bold mb-6">Property Geocoding Admin</h1>
        
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-1">
            <div className="bg-white rounded-lg shadow p-4 mb-4">
              <h2 className="text-xl font-semibold mb-4">Geocoding Stats</h2>
              
              {loading ? (
                <div className="flex justify-center py-4">
                  <div className="w-8 h-8 border-4 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
                </div>
              ) : stats ? (
                <div className="space-y-3">
                  <div>
                    <h3 className="text-sm font-medium text-gray-500">Properties with Coordinates</h3>
                    <p className="text-2xl font-bold">{stats.properties_with_coordinates}</p>
                    <p className="text-sm text-gray-500">{stats.geocoded_percent}% of total properties</p>
                  </div>
                  
                  <div>
                    <h3 className="text-sm font-medium text-gray-500">Properties without Coordinates</h3>
                    <p className="text-2xl font-bold">{stats.total_properties - stats.properties_with_coordinates}</p>
                  </div>
                  
                  <div>
                    <h3 className="text-sm font-medium text-gray-500">Verified Properties</h3>
                    <p className="text-2xl font-bold">{stats.verified_properties || 0}</p>
                    <p className="text-sm text-gray-500">{stats.verified_percent || 0}% of geocoded properties</p>
                  </div>
                  
                  <div>
                    <h3 className="text-sm font-medium text-gray-500">Total Properties</h3>
                    <p className="text-2xl font-bold">{stats.total_properties}</p>
                  </div>
                  
                  <button
                    onClick={loadStats}
                    className="w-full mt-4 py-2 bg-gray-100 rounded hover:bg-gray-200 text-gray-800"
                  >
                    Refresh Stats
                  </button>
                </div>
              ) : (
                <div className="text-gray-500">No stats available</div>
              )}
            </div>
            
            <div className="bg-white rounded-lg shadow p-4 mb-4">
              <h2 className="text-xl font-semibold mb-4">Run Batch Geocoding</h2>
              
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Batch Size
                  </label>
                  <input
                    type="number"
                    value={batchSize}
                    onChange={(e) => setBatchSize(Math.max(1, parseInt(e.target.value) || 1))}
                    className="w-full p-2 border rounded"
                    min="1"
                    max="1000"
                  />
                  <p className="text-xs text-gray-500 mt-1">
                    Number of properties to process in this batch (1-1000)
                  </p>
                </div>
                
                <div className="flex items-center">
                  <input
                    type="checkbox"
                    id="force-refresh"
                    checked={forceRefresh}
                    onChange={(e) => setForceRefresh(e.target.checked)}
                    className="h-4 w-4 text-blue-600 border-gray-300 rounded"
                  />
                  <label htmlFor="force-refresh" className="ml-2 text-sm text-gray-700">
                    Force refresh existing coordinates
                  </label>
                </div>
                
                <button
                  onClick={handleStartGeocodingTask}
                  disabled={loading}
                  className="w-full py-2 bg-blue-500 text-white rounded hover:bg-blue-600 disabled:opacity-50"
                >
                  {loading ? 'Processing...' : 'Start Geocoding Task'}
                </button>
              </div>
            </div>
            
            <div className="bg-white rounded-lg shadow p-4">
              <h2 className="text-xl font-semibold mb-4">Verify Coordinates</h2>
              <p className="text-sm text-gray-600 mb-3">
                Analyze existing properties to ensure that their coordinates match their addresses using Google Maps API.
              </p>
              
              <div className="space-y-4">
                <div>
                  <h3 className="font-semibold mb-2">Verification Options:</h3>
                  <div className="flex flex-col space-y-2">
                    <label className="flex items-center space-x-2">
                      <input
                        type="checkbox"
                        checked={coordinateVerificationCheckSuspicious}
                        onChange={(e) => {
                          setCoordinateVerificationCheckSuspicious(e.target.checked);
                          if (e.target.checked) {
                            setCoordinateVerificationCheckAll(false);
                          }
                        }}
                        className="form-checkbox"
                      />
                      <span>Check potentially incorrect coordinates (outside Austin area, etc.)</span>
                    </label>
                    
                    <label className="flex items-center space-x-2">
                      <input
                        type="checkbox"
                        checked={coordinateVerificationCheckAll}
                        onChange={(e) => {
                          setCoordinateVerificationCheckAll(e.target.checked);
                          if (e.target.checked) {
                            setCoordinateVerificationCheckSuspicious(false);
                          }
                        }}
                        className="form-checkbox"
                      />
                      <span>Re-verify all properties with coordinates</span>
                    </label>
                  </div>
                </div>
                
                <div>
                  <label className="block mb-2">
                    Batch Size (1-500):
                    <input
                      type="number"
                      value={coordinateVerificationBatchSize}
                      onChange={(e) => setCoordinateVerificationBatchSize(
                        Math.min(Math.max(1, parseInt(e.target.value) || 1), 500)
                      )}
                      min="1"
                      max="500"
                      className="form-input ml-2 w-24"
                    />
                  </label>
                  <p className="text-sm text-gray-500">Larger batches will take longer to process</p>
                </div>
                
                <div>
                  <label className="flex items-center space-x-2">
                    <input
                      type="checkbox"
                      checked={coordinateVerificationAutoFix}
                      onChange={(e) => setCoordinateVerificationAutoFix(e.target.checked)}
                      className="form-checkbox"
                    />
                    <span>Automatically fix incorrect coordinates</span>
                  </label>
                  <p className="text-sm text-gray-500">
                    Properties with coordinates more than 100 meters off will be updated with Google Maps data
                  </p>
                </div>
                
                <button
                  onClick={handleVerifyCoordinates}
                  disabled={isLoading || (!coordinateVerificationCheckAll && !coordinateVerificationCheckSuspicious)}
                  className={`bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700 ${
                    isLoading || (!coordinateVerificationCheckAll && !coordinateVerificationCheckSuspicious)
                      ? 'opacity-50 cursor-not-allowed'
                      : ''
                  }`}
                >
                  {isLoading ? 'Processing...' : 'Verify Coordinates'}
                </button>
              </div>
            </div>
          </div>
          
          <div className="lg:col-span-2">
            <h2 className="text-xl font-semibold mb-4">Recent Geocoding Tasks</h2>
            
            {recentTasks.length > 0 ? (
              recentTasks.map((taskId) => (
                <TaskItem 
                  key={taskId} 
                  taskId={taskId} 
                  onRefresh={loadStats} 
                />
              ))
            ) : (
              <div className="bg-white rounded-lg shadow p-6 text-center text-gray-500">
                No recent tasks. Start a new geocoding task to see results here.
              </div>
            )}
          </div>
        </div>
      </div>
    </Layout>
  );
} 