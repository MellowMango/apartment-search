# Geocoding Fix Instructions

This document provides instructions for fixing geocoding functionality in the Acquire application.

## 1. Run SQL to Add Geocode Verification Column

Run the following SQL in your Supabase SQL Editor:

```sql
-- Add geocode_verified column to properties table if it doesn't exist
ALTER TABLE properties ADD COLUMN IF NOT EXISTS geocode_verified BOOLEAN DEFAULT FALSE;

-- Update existing properties with coordinates to have geocode_verified = true
UPDATE properties 
SET geocode_verified = TRUE 
WHERE 
    latitude IS NOT NULL 
    AND longitude IS NOT NULL 
    AND latitude != 0 
    AND longitude != 0;

-- Check the results
SELECT 
    COUNT(*) as total_properties,
    SUM(CASE WHEN geocode_verified = TRUE THEN 1 ELSE 0 END) as verified_properties,
    SUM(CASE WHEN latitude IS NOT NULL AND longitude IS NOT NULL AND latitude <> 0 AND longitude <> 0 THEN 1 ELSE 0 END) as properties_with_coordinates
FROM properties;
```

## 2. Update Frontend Port Configuration

The frontend is configured to run on port 3002, but the package.json file might still specify port 3000. Update the dev script in the package.json file:

```bash
cd /Users/guyma/code/projects/acquire/frontend
# Edit package.json to update the dev script
# Change:
# "dev": "next dev -p 3000",
# To:
# "dev": "next dev -p 3002",
```

## 3. Ensure Backend API is Running

The backend API needs to be running as it contains the geocoding routes.

```bash
cd /Users/guyma/code/projects/acquire/backend
python -m app.main
```

This will start the FastAPI server at http://localhost:8000. The geocoding routes are already included in the backend's main.py file.

## 4. Restart the Frontend Application

The frontend may be experiencing issues connecting to the backend. Let's restart it:

```bash
cd /Users/guyma/code/projects/acquire/frontend
# Stop any existing processes
pkill -f "next dev"
# Start the frontend
npm run dev
```

Once the frontend is running, you can access the geocoding admin page at:
http://localhost:3002/admin/geocoding

Note that the application is running on port 3002, not the default 3000.

## How It Works

1. The `geocode_verified` column in the properties table tracks which properties have verified coordinates
2. The backend API provides these endpoints:
   - GET `/api/v1/admin/geocoding/geocode-stats` - Retrieves statistics about geocoded properties
   - POST `/api/v1/admin/geocoding/geocode-batch` - Triggers batch geocoding for properties
   - GET `/api/v1/admin/geocoding/geocode-status/{task_id}` - Checks the status of a geocoding task

3. The frontend connects to these endpoints to display statistics and manage geocoding

## Troubleshooting

- If you see a 500 error with the geocoding stats endpoint, make sure you've added the `geocode_verified` column using the SQL above
- If you get a 404 error, ensure you're using the correct port (3002) for the frontend
- Make sure the backend server is running on port 8000
- Check your browser console for network errors or JavaScript errors
- If you're still experiencing issues, verify the environment variables in both frontend/.env and backend/.env files 