-- Brokerages Table
CREATE TABLE IF NOT EXISTS brokerages (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  name TEXT NOT NULL,
  website TEXT,
  logo_url TEXT,
  address TEXT,
  city TEXT DEFAULT 'Austin',
  state TEXT DEFAULT 'TX',
  zip_code TEXT,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Enable Row Level Security
ALTER TABLE brokerages ENABLE ROW LEVEL SECURITY;

-- Create policies
-- Note: We'll drop existing policies first to avoid errors
DROP POLICY IF EXISTS "Brokerages are viewable by everyone" ON brokerages;
CREATE POLICY "Brokerages are viewable by everyone" 
  ON brokerages FOR SELECT USING (true);

DROP POLICY IF EXISTS "Brokerages are editable by authenticated users" ON brokerages;
CREATE POLICY "Brokerages are editable by authenticated users" 
  ON brokerages FOR UPDATE USING (auth.role() = 'authenticated');

DROP POLICY IF EXISTS "Brokerages are insertable by authenticated users" ON brokerages;
CREATE POLICY "Brokerages are insertable by authenticated users" 
  ON brokerages FOR INSERT WITH CHECK (auth.role() = 'authenticated');

-- Check if brokerage_id column exists in properties table, add it if it doesn't
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_name = 'properties'
        AND column_name = 'brokerage_id'
    ) THEN
        ALTER TABLE properties ADD COLUMN brokerage_id UUID;
    END IF;
END $$;

-- Add foreign key constraint to properties table
ALTER TABLE properties 
  DROP CONSTRAINT IF EXISTS fk_properties_brokerage;
  
ALTER TABLE properties 
  ADD CONSTRAINT fk_properties_brokerage 
  FOREIGN KEY (brokerage_id) 
  REFERENCES brokerages(id) 
  ON DELETE SET NULL;

-- Create trigger to update the updated_at column
DROP TRIGGER IF EXISTS update_brokerages_updated_at ON brokerages;
CREATE TRIGGER update_brokerages_updated_at
  BEFORE UPDATE ON brokerages
  FOR EACH ROW EXECUTE FUNCTION update_updated_at_column(); 