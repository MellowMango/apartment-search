-- Add columns for tracking non-multifamily properties

-- Check if columns exist before adding them
DO $$
BEGIN
    -- Add is_multifamily column if it doesn't exist
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'properties' AND column_name = 'is_multifamily') THEN
        ALTER TABLE properties ADD COLUMN is_multifamily BOOLEAN DEFAULT TRUE;
    END IF;

    -- Add non_multifamily_detected column if it doesn't exist
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'properties' AND column_name = 'non_multifamily_detected') THEN
        ALTER TABLE properties ADD COLUMN non_multifamily_detected BOOLEAN DEFAULT FALSE;
    END IF;

    -- Add cleaning_note column if it doesn't exist
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'properties' AND column_name = 'cleaning_note') THEN
        ALTER TABLE properties ADD COLUMN cleaning_note TEXT;
    END IF;
END
$$;

-- Create view for multifamily properties only
DROP VIEW IF EXISTS multifamily_properties;
CREATE VIEW multifamily_properties AS
SELECT * FROM properties 
WHERE (non_multifamily_detected IS NOT TRUE OR non_multifamily_detected IS NULL)
AND (is_multifamily IS NOT FALSE OR is_multifamily IS NULL);

-- Add an index to improve query performance
CREATE INDEX IF NOT EXISTS idx_properties_multifamily ON properties (is_multifamily, non_multifamily_detected);