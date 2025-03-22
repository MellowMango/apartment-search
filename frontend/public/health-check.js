/**
 * Health check script for Acquire application
 * This script uses relative URLs to check the connection to the server
 * instead of hardcoded localhost:3000 references
 */
 
// Get the current host (including port) from the window location
const currentHost = window.location.host;
const protocol = window.location.protocol;

// Function to check the health of the API
async function checkApiHealth() {
  try {
    // Use a relative URL that will work regardless of port
    const response = await fetch('/api/health');
    
    if (response.ok) {
      console.log('API health check successful');
      return true;
    } else {
      console.error('API health check failed with status:', response.status);
      return false;
    }
  } catch (error) {
    console.error('API health check error:', error);
    return false;
  }
}

// Execute the health check once
checkApiHealth(); 