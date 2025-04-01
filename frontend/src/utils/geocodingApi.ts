/**
 * Geocoding API utility functions
 * 
 * These utilities provide an interface to the backend geocoding API endpoints
 * to trigger batch geocoding of properties and retrieve statistics.
 */

import { supabase } from './supabase';

/**
 * Helper function to get the base URL for API requests
 * This ensures requests go to the correct backend API URL
 * regardless of which port the frontend is running on
 */
function getApiBaseUrl(): string {
  // For production use the configured API URL
  return process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';
}

/**
 * Trigger a batch geocoding task for properties without coordinates
 * 
 * @param batchSize Number of properties to geocode in this batch
 * @param forceRefresh Whether to refresh properties that already have coordinates
 * @returns Task ID that can be used to check status
 */
export async function triggerBatchGeocode(batchSize = 100, forceRefresh = false): Promise<{task_id: string}> {
  try {
    // Get the authenticated session
    const { data: { session } } = await supabase.auth.getSession();
    
    if (!session) {
      throw new Error('Authentication required to trigger geocoding');
    }
    
    // Make the API request to the backend API (not the Next.js API route)
    const response = await fetch(`${getApiBaseUrl()}/admin/geocoding/geocode-batch`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${session.access_token}`
      },
      body: JSON.stringify({
        batch_size: batchSize,
        force_refresh: forceRefresh
      })
    });
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to trigger batch geocoding');
    }
    
    return await response.json();
  } catch (error) {
    console.error('Error triggering batch geocoding:', error);
    throw error;
  }
}

/**
 * Check the status of a geocoding task
 * 
 * @param taskId ID of the task to check
 * @returns Task status information
 */
export async function checkGeocodingTaskStatus(taskId: string) {
  try {
    // Get the authenticated session
    const { data: { session } } = await supabase.auth.getSession();
    
    if (!session) {
      throw new Error('Authentication required to check geocoding task status');
    }
    
    // Make the API request to the backend API
    const response = await fetch(`${getApiBaseUrl()}/admin/geocoding/geocode-status/${taskId}`, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${session.access_token}`
      }
    });
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to check geocoding task status');
    }
    
    return await response.json();
  } catch (error) {
    console.error('Error checking geocoding task status:', error);
    throw error;
  }
}

/**
 * Get statistics about property geocoding
 * 
 * @returns Geocoding statistics
 */
export async function getGeocodingStats() {
  try {
    // Get the authenticated session
    const { data: { session } } = await supabase.auth.getSession();
    
    if (!session) {
      throw new Error('Authentication required to get geocoding stats');
    }
    
    // Make the API request directly to the backend API
    const response = await fetch(`${getApiBaseUrl()}/admin/geocoding/geocode-stats`, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${session.access_token}`
      }
    });
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to get geocoding statistics');
    }
    
    return await response.json();
  } catch (error) {
    console.error('Error getting geocoding statistics:', error);
    throw error;
  }
}

/**
 * Triggers a coordinate verification task to check and potentially fix coordinates
 * against Google Maps API
 * @param options Configuration options for verification
 * @returns Task ID that can be used to check status
 */
export async function verifyCoordinates(options: {
  batchSize?: number;
  checkAll?: boolean;
  autoFix?: boolean;
}): Promise<string> {
  const { batchSize = 50, checkAll = false, autoFix = true } = options;
  
  try {
    // Get the authenticated session
    const { data: { session } } = await supabase.auth.getSession();
    
    if (!session) {
      throw new Error('Authentication required to verify coordinates');
    }
    
    const response = await fetch(`${getApiBaseUrl()}/admin/geocoding/verify-coordinates`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${session.access_token}`
      },
      body: JSON.stringify({
        batch_size: batchSize,
        check_all: checkAll,
        auto_fix: autoFix
      })
    });
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.error || 'Failed to start coordinate verification task');
    }
    
    const data = await response.json();
    return data.task_id;
    
  } catch (error) {
    console.error('Error starting coordinate verification task:', error);
    throw error;
  }
}

/**
 * Get detailed results for a coordinate verification task
 * 
 * @param taskId The ID of the verification task
 * @returns Detailed verification results including metadata
 */
export async function getVerificationTaskResults(taskId: string) {
  try {
    // Get the authenticated session
    const { data: { session } } = await supabase.auth.getSession();
    
    if (!session) {
      throw new Error('Authentication required to view verification results');
    }
    
    // First get the task status which includes basic info
    const taskStatus = await checkGeocodingTaskStatus(taskId);
    
    // If task isn't completed or has no metadata, return the basic status
    if (taskStatus.status !== 'completed' || !taskStatus.metadata) {
      return taskStatus;
    }
    
    // Add some helpful statistics about the verification results
    const results = taskStatus.metadata.results || [];
    
    // Group results by distance ranges
    const distanceRanges = {
      accurate: 0, // Less than 10 meters
      minor: 0,    // 10-100 meters
      major: 0,    // 100-1000 meters
      extreme: 0,  // Over 1000 meters
      errors: 0    // Verification errors
    };
    
    results.forEach((result: { verified: boolean; distance: number }) => {
      if (!result.verified) {
        distanceRanges.errors++;
      } else if (result.distance < 10) {
        distanceRanges.accurate++;
      } else if (result.distance < 100) {
        distanceRanges.minor++;
      } else if (result.distance < 1000) {
        distanceRanges.major++;
      } else {
        distanceRanges.extreme++;
      }
    });
    
    return {
      ...taskStatus,
      verificationStats: {
        total: results.length,
        distanceRanges,
        updatedCount: taskStatus.metadata.updatedCount || 0
      }
    };
  } catch (error) {
    console.error('Error getting verification task results:', error);
    throw error;
  }
} 