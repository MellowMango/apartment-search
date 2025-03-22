import { useState, useEffect } from 'react';
import { useRouter } from 'next/router';
import { supabase } from '../../lib/supabase';
import Layout from '../../src/components/Layout';
import { triggerBatchGeocode, getGeocodingStats, checkGeocodingTaskStatus, verifyCoordinates, getVerificationTaskResults } from '../../src/utils/geocodingApi';

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

  const handleCheckTask = async (taskId) => {
    try {
      setIsLoading(true);
      // Get basic task info first
      const basicTaskInfo = await checkGeocodingTaskStatus(taskId);
      
      // Get detailed task status with the appropriate function based on task type
      let taskData;
      if (basicTaskInfo.task_type === "verify_coordinates") {
        taskData = await getVerificationTaskResults(taskId);
      } else {
        // For regular geocoding tasks
        taskData = basicTaskInfo;
      }
      
      // Display results
      alert(`
        Task ID: ${taskData.id}
        Status: ${taskData.status}
        Started: ${new Date(taskData.start_time).toLocaleString()}
        ${taskData.end_time ? `Completed: ${new Date(taskData.end_time).toLocaleString()}` : 'Not completed yet'}
        ${taskData.progress ? `Progress: ${taskData.progress}%` : ''}
        ${taskData.success_count !== undefined ? `Success: ${taskData.success_count}` : ''}
        ${taskData.error_count !== undefined ? `Errors: ${taskData.error_count}` : ''}
        ${taskData.total_count !== undefined ? `Total: ${taskData.total_count}` : ''}
      `);
      
      // Refresh stats after checking task
      loadStats();
    } catch (err) {
      console.error('Failed to check task status:', err);
      alert('Failed to check task status: ' + err.message);
    } finally {
      setIsLoading(false);
    }
  };

  if (!isAdmin) {
    return (
      <Layout>
        <div className="container mx-auto px-4 py-8">
          <p>Please log in with administrator privileges.</p>
        </div>
      </Layout>
    );
  }

  return (
    <Layout title="Geocoding Admin | Austin Multifamily Map">
      <div className="container mx-auto px-4 py-8">
        <h1 className="text-2xl font-bold mb-6">Geocoding Administration</h1>
        
        {/* Stats Section */}
        <div className="bg-white shadow rounded-lg p-6 mb-8">
          <h2 className="text-xl font-semibold mb-4">Geocoding Statistics</h2>
          
          {loading ? (
            <p>Loading statistics...</p>
          ) : stats ? (
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="bg-blue-50 p-4 rounded">
                <h3 className="text-lg font-medium text-blue-800">Total Properties</h3>
                <p className="text-3xl font-bold">{stats.total_properties}</p>
              </div>
              
              <div className="bg-green-50 p-4 rounded">
                <h3 className="text-lg font-medium text-green-800">Geocoded</h3>
                <p className="text-3xl font-bold">{stats.properties_with_coordinates}</p>
                <p className="text-sm mt-1">
                  {stats.geocoded_percent}% of total
                </p>
              </div>
              
              <div className="bg-yellow-50 p-4 rounded">
                <h3 className="text-lg font-medium text-yellow-800">Verified</h3>
                <p className="text-3xl font-bold">{stats.verified_properties || 0}</p>
                <p className="text-sm mt-1">
                  {stats.verified_percent || 0}% of geocoded
                </p>
              </div>
            </div>
          ) : (
            <p>Failed to load statistics.</p>
          )}
          
          <div className="mt-4">
            <button 
              onClick={loadStats} 
              className="text-blue-600 hover:text-blue-800 text-sm"
              disabled={loading}
            >
              {loading ? 'Refreshing...' : 'Refresh Statistics'}
            </button>
          </div>
        </div>
        
        {/* Batch Geocoding Section */}
        <div className="bg-white shadow rounded-lg p-6 mb-8">
          <h2 className="text-xl font-semibold mb-4">Batch Geocoding</h2>
          
          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Batch Size (max 500)
            </label>
            <input
              type="number"
              min="1"
              max="500"
              value={batchSize}
              onChange={(e) => setBatchSize(Math.min(500, Math.max(1, parseInt(e.target.value) || 1)))}
              className="w-full md:w-1/4 p-2 border rounded"
            />
          </div>
          
          <div className="mb-4">
            <label className="flex items-center text-sm font-medium text-gray-700">
              <input
                type="checkbox"
                checked={forceRefresh}
                onChange={(e) => setForceRefresh(e.target.checked)}
                className="mr-2"
              />
              Reprocess properties that already have coordinates
            </label>
          </div>
          
          <button
            onClick={handleStartGeocodingTask}
            disabled={loading}
            className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700 disabled:opacity-50"
          >
            {loading ? 'Processing...' : 'Start Batch Geocoding'}
          </button>
        </div>
        
        {/* Coordinate Verification Section */}
        <div className="bg-white shadow rounded-lg p-6 mb-8">
          <h2 className="text-xl font-semibold mb-4">Verify Coordinates</h2>
          <p className="mb-4 text-gray-600">
            Analyze existing properties to ensure their coordinates match their addresses using Google Maps.
          </p>
          
          <div className="space-y-4 mb-6">
            <div>
              <label className="flex items-center text-sm font-medium text-gray-700">
                <input
                  type="checkbox"
                  checked={coordinateVerificationCheckSuspicious}
                  onChange={(e) => setCoordinateVerificationCheckSuspicious(e.target.checked)}
                  className="mr-2"
                />
                Check potentially incorrect coordinates (recommended)
              </label>
            </div>
            
            <div>
              <label className="flex items-center text-sm font-medium text-gray-700">
                <input
                  type="checkbox"
                  checked={coordinateVerificationCheckAll}
                  onChange={(e) => setCoordinateVerificationCheckAll(e.target.checked)}
                  className="mr-2"
                />
                Re-verify all properties with coordinates
              </label>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Batch Size (max 500)
              </label>
              <input
                type="number"
                min="1"
                max="500"
                value={coordinateVerificationBatchSize}
                onChange={(e) => setCoordinateVerificationBatchSize(
                  Math.min(500, Math.max(1, parseInt(e.target.value) || 50))
                )}
                className="w-full md:w-1/4 p-2 border rounded"
              />
            </div>
            
            <div>
              <label className="flex items-center text-sm font-medium text-gray-700">
                <input
                  type="checkbox"
                  checked={coordinateVerificationAutoFix}
                  onChange={(e) => setCoordinateVerificationAutoFix(e.target.checked)}
                  className="mr-2"
                />
                Automatically fix incorrect coordinates
              </label>
            </div>
          </div>
          
          <button
            onClick={handleVerifyCoordinates}
            disabled={isLoading}
            className="bg-green-600 text-white px-4 py-2 rounded hover:bg-green-700 disabled:opacity-50"
          >
            {isLoading ? 'Processing...' : 'Verify Coordinates'}
          </button>
        </div>
        
        {/* Recent Tasks Section */}
        {recentTasks.length > 0 && (
          <div className="bg-white shadow rounded-lg p-6">
            <h2 className="text-xl font-semibold mb-4">Recent Tasks</h2>
            
            {recentTasks.map((taskId) => (
              <TaskItem key={taskId} taskId={taskId} onRefresh={loadStats} />
            ))}
          </div>
        )}
      </div>
    </Layout>
  );
} 