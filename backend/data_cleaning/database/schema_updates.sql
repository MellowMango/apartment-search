-- Create a table for storing cleaning logs
CREATE TABLE IF NOT EXISTS cleaning_logs (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  log_type TEXT NOT NULL,
  log_data JSONB NOT NULL,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create a table for storing property review candidates
CREATE TABLE IF NOT EXISTS property_review_candidates (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  review_id TEXT NOT NULL UNIQUE,
  review_type TEXT NOT NULL,
  primary_property_id UUID REFERENCES properties(id) ON DELETE SET NULL,
  secondary_property_id UUID REFERENCES properties(id) ON DELETE SET NULL,
  property_id UUID REFERENCES properties(id) ON DELETE SET NULL,
  reason TEXT NOT NULL,
  reason_details JSONB,
  proposed_action TEXT NOT NULL,
  approved BOOLEAN,
  review_notes TEXT,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  reviewed_at TIMESTAMP WITH TIME ZONE,
  applied_at TIMESTAMP WITH TIME ZONE
);

-- Create a table for storing property metadata
CREATE TABLE IF NOT EXISTS property_metadata (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  property_id UUID NOT NULL REFERENCES properties(id) ON DELETE CASCADE,
  metadata_key TEXT NOT NULL,
  metadata_value JSONB NOT NULL,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  UNIQUE(property_id, metadata_key)
);

-- Enable Row Level Security
ALTER TABLE cleaning_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE property_review_candidates ENABLE ROW LEVEL SECURITY;
ALTER TABLE property_metadata ENABLE ROW LEVEL SECURITY;

-- Create policies
CREATE POLICY "Cleaning logs are viewable by authenticated users" 
  ON cleaning_logs FOR SELECT USING (auth.role() = 'authenticated');

CREATE POLICY "Cleaning logs are insertable by authenticated users" 
  ON cleaning_logs FOR INSERT WITH CHECK (auth.role() = 'authenticated');

CREATE POLICY "Property review candidates are viewable by authenticated users" 
  ON property_review_candidates FOR SELECT USING (auth.role() = 'authenticated');

CREATE POLICY "Property review candidates are editable by authenticated users" 
  ON property_review_candidates FOR UPDATE USING (auth.role() = 'authenticated');

CREATE POLICY "Property review candidates are insertable by authenticated users" 
  ON property_review_candidates FOR INSERT WITH CHECK (auth.role() = 'authenticated');

CREATE POLICY "Property metadata is viewable by authenticated users" 
  ON property_metadata FOR SELECT USING (auth.role() = 'authenticated');

CREATE POLICY "Property metadata is editable by authenticated users" 
  ON property_metadata FOR UPDATE USING (auth.role() = 'authenticated');

CREATE POLICY "Property metadata is insertable by authenticated users" 
  ON property_metadata FOR INSERT WITH CHECK (auth.role() = 'authenticated');

CREATE POLICY "Property metadata is deletable by authenticated users" 
  ON property_metadata FOR DELETE USING (auth.role() = 'authenticated'); 