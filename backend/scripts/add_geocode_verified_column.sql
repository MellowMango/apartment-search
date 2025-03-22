-- Add geocode_verified column to properties table
-- This migration adds a boolean column to track verified property coordinates

-- Check if column exists first to make it idempotent
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT FROM information_schema.columns 
        WHERE table_name = 'properties' AND column_name = 'geocode_verified'
    ) THEN
        ALTER TABLE properties ADD COLUMN geocode_verified BOOLEAN DEFAULT FALSE;
        
        -- Update existing properties with coordinates to have geocode_verified = true
        UPDATE properties 
        SET geocode_verified = TRUE 
        WHERE 
            latitude IS NOT NULL AND 
            longitude IS NOT NULL AND 
            latitude != 0 AND 
            longitude != 0;
            
        RAISE NOTICE 'Added geocode_verified column to properties table';
    ELSE
        RAISE NOTICE 'geocode_verified column already exists in properties table';
    END IF;
END $$; 