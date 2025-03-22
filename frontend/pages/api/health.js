/**
 * Simple health check endpoint
 * Used to verify the API server is running
 */
export default function handler(req, res) {
  res.status(200).json({ 
    status: 'ok',
    timestamp: new Date().toISOString()
  });
} 