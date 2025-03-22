 -- Acquire Apartments Database Schema
-- This file contains the complete database schema for the Acquire Apartments application

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Properties Table
CREATE TABLE IF NOT EXISTS properties (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  name TEXT NOT NULL,
  address TEXT NOT NULL,
  city TEXT NOT NULL DEFAULT 'Austin',
  state TEXT NOT NULL DEFAULT 'TX',
  zip_code TEXT,
  latitude NUMERIC,
  longitude NUMERIC,
  geocode_verified BOOLEAN DEFAULT FALSE,
  price NUMERIC,
  units INTEGER,
  year_built INTEGER,
  year_renovated INTEGER,
  square_feet NUMERIC,
  price_per_unit NUMERIC,
  price_per_sqft NUMERIC,
  cap_rate NUMERIC,
  property_type TEXT,
  property_status TEXT DEFAULT 'active',
  property_website TEXT,
  listing_website TEXT,
  call_for_offers_date TIMESTAMP WITH TIME ZONE,
  description TEXT,
  amenities JSONB,
  images JSONB,
  broker_id UUID,
  brokerage_id UUID,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  date_first_appeared TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Enable Row Level Security
ALTER TABLE properties ENABLE ROW LEVEL SECURITY;

-- Create policies
DROP POLICY IF EXISTS "Properties are viewable by everyone" ON properties;
CREATE POLICY "Properties are viewable by everyone" 
  ON properties FOR SELECT USING (true);

DROP POLICY IF EXISTS "Properties are editable by authenticated users" ON properties;
CREATE POLICY "Properties are editable by authenticated users" 
  ON properties FOR UPDATE USING (auth.role() = 'authenticated');

DROP POLICY IF EXISTS "Properties are insertable by authenticated users" ON properties;
CREATE POLICY "Properties are insertable by authenticated users" 
  ON properties FOR INSERT WITH CHECK (auth.role() = 'authenticated');

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
DROP POLICY IF EXISTS "Brokerages are viewable by everyone" ON brokerages;
CREATE POLICY "Brokerages are viewable by everyone" 
  ON brokerages FOR SELECT USING (true);

DROP POLICY IF EXISTS "Brokerages are editable by authenticated users" ON brokerages;
CREATE POLICY "Brokerages are editable by authenticated users" 
  ON brokerages FOR UPDATE USING (auth.role() = 'authenticated');

DROP POLICY IF EXISTS "Brokerages are insertable by authenticated users" ON brokerages;
CREATE POLICY "Brokerages are insertable by authenticated users" 
  ON brokerages FOR INSERT WITH CHECK (auth.role() = 'authenticated');

-- Brokers Table
CREATE TABLE IF NOT EXISTS brokers (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  name TEXT NOT NULL,
  company TEXT,
  email TEXT,
  phone TEXT,
  website TEXT,
  brokerage_id UUID REFERENCES brokerages(id),
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Enable Row Level Security
ALTER TABLE brokers ENABLE ROW LEVEL SECURITY;

-- Create policies
DROP POLICY IF EXISTS "Brokers are viewable by everyone" ON brokers;
CREATE POLICY "Brokers are viewable by everyone" 
  ON brokers FOR SELECT USING (true);

DROP POLICY IF EXISTS "Brokers are editable by authenticated users" ON brokers;
CREATE POLICY "Brokers are editable by authenticated users" 
  ON brokers FOR UPDATE USING (auth.role() = 'authenticated');

DROP POLICY IF EXISTS "Brokers are insertable by authenticated users" ON brokers;
CREATE POLICY "Brokers are insertable by authenticated users" 
  ON brokers FOR INSERT WITH CHECK (auth.role() = 'authenticated');

-- Check if broker_id column exists in properties table, add it if it doesn't
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_name = 'properties'
        AND column_name = 'broker_id'
    ) THEN
        ALTER TABLE properties ADD COLUMN broker_id UUID;
    END IF;
END $$;

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
  DROP CONSTRAINT IF EXISTS fk_properties_broker;
  
ALTER TABLE properties 
  ADD CONSTRAINT fk_properties_broker 
  FOREIGN KEY (broker_id) 
  REFERENCES brokers(id) 
  ON DELETE SET NULL;

ALTER TABLE properties 
  DROP CONSTRAINT IF EXISTS fk_properties_brokerage;
  
ALTER TABLE properties 
  ADD CONSTRAINT fk_properties_brokerage 
  FOREIGN KEY (brokerage_id) 
  REFERENCES brokerages(id) 
  ON DELETE SET NULL;

-- User Profiles Table (Extended Profile)
CREATE TABLE IF NOT EXISTS user_profiles (
  id UUID PRIMARY KEY REFERENCES auth.users,
  full_name TEXT,
  company TEXT,
  job_title TEXT,
  phone TEXT,
  avatar_url TEXT,
  subscription_tier TEXT DEFAULT 'free',
  subscription_status TEXT DEFAULT 'active',
  stripe_customer_id TEXT,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Enable Row Level Security
ALTER TABLE user_profiles ENABLE ROW LEVEL SECURITY;

-- Create policies
DROP POLICY IF EXISTS "User profiles are viewable by the user" ON user_profiles;
CREATE POLICY "User profiles are viewable by the user" 
  ON user_profiles FOR SELECT USING (auth.uid() = id);

DROP POLICY IF EXISTS "User profiles are editable by the user" ON user_profiles;
CREATE POLICY "User profiles are editable by the user" 
  ON user_profiles FOR UPDATE USING (auth.uid() = id);

DROP POLICY IF EXISTS "User profiles are insertable by the user" ON user_profiles;
CREATE POLICY "User profiles are insertable by the user" 
  ON user_profiles FOR INSERT WITH CHECK (auth.uid() = id);

-- Subscriptions Table
CREATE TABLE IF NOT EXISTS subscriptions (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID REFERENCES auth.users NOT NULL,
  stripe_subscription_id TEXT,
  tier TEXT NOT NULL,
  status TEXT NOT NULL,
  current_period_start TIMESTAMP WITH TIME ZONE,
  current_period_end TIMESTAMP WITH TIME ZONE,
  cancel_at_period_end BOOLEAN DEFAULT FALSE,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Enable Row Level Security
ALTER TABLE subscriptions ENABLE ROW LEVEL SECURITY;

-- Create policies
DROP POLICY IF EXISTS "Subscriptions are viewable by the user" ON subscriptions;
CREATE POLICY "Subscriptions are viewable by the user" 
  ON subscriptions FOR SELECT USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Subscriptions are editable by the user" ON subscriptions;
CREATE POLICY "Subscriptions are editable by the user" 
  ON subscriptions FOR UPDATE USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Subscriptions are insertable by the user" ON subscriptions;
CREATE POLICY "Subscriptions are insertable by the user" 
  ON subscriptions FOR INSERT WITH CHECK (auth.uid() = user_id);

-- Saved Properties Table (for users to save properties they're interested in)
CREATE TABLE IF NOT EXISTS saved_properties (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID REFERENCES auth.users NOT NULL,
  property_id UUID REFERENCES properties(id) NOT NULL,
  notes TEXT,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  UNIQUE(user_id, property_id)
);

-- Enable Row Level Security
ALTER TABLE saved_properties ENABLE ROW LEVEL SECURITY;

-- Create policies
DROP POLICY IF EXISTS "Saved properties are viewable by the user" ON saved_properties;
CREATE POLICY "Saved properties are viewable by the user" 
  ON saved_properties FOR SELECT USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Saved properties are editable by the user" ON saved_properties;
CREATE POLICY "Saved properties are editable by the user" 
  ON saved_properties FOR UPDATE USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Saved properties are insertable by the user" ON saved_properties;
CREATE POLICY "Saved properties are insertable by the user" 
  ON saved_properties FOR INSERT WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS "Saved properties are deletable by the user" ON saved_properties;
CREATE POLICY "Saved properties are deletable by the user" 
  ON saved_properties FOR DELETE USING (auth.uid() = user_id);

-- Property Notes Table (for admin users to add notes about properties)
CREATE TABLE IF NOT EXISTS property_notes (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  property_id UUID REFERENCES properties(id) NOT NULL,
  user_id UUID REFERENCES auth.users NOT NULL,
  note TEXT NOT NULL,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Enable Row Level Security
ALTER TABLE property_notes ENABLE ROW LEVEL SECURITY;

-- Create policies
DROP POLICY IF EXISTS "Property notes are viewable by authenticated users" ON property_notes;
CREATE POLICY "Property notes are viewable by authenticated users" 
  ON property_notes FOR SELECT USING (auth.role() = 'authenticated');

DROP POLICY IF EXISTS "Property notes are editable by the creator" ON property_notes;
CREATE POLICY "Property notes are editable by the creator" 
  ON property_notes FOR UPDATE USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Property notes are insertable by authenticated users" ON property_notes;
CREATE POLICY "Property notes are insertable by authenticated users" 
  ON property_notes FOR INSERT WITH CHECK (auth.role() = 'authenticated');

DROP POLICY IF EXISTS "Property notes are deletable by the creator" ON property_notes;
CREATE POLICY "Property notes are deletable by the creator" 
  ON property_notes FOR DELETE USING (auth.uid() = user_id);

-- Create a function to handle user creation
CREATE OR REPLACE FUNCTION public.handle_new_user() 
RETURNS TRIGGER AS $$
BEGIN
  INSERT INTO public.user_profiles (id, full_name)
  VALUES (new.id, new.raw_user_meta_data->>'full_name');
  RETURN new;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Create a trigger to call the function when a new user is created
DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
CREATE TRIGGER on_auth_user_created
  AFTER INSERT ON auth.users
  FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();

-- Create a function to update the updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
   NEW.updated_at = NOW();
   RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers to update the updated_at column for all tables
DROP TRIGGER IF EXISTS update_properties_updated_at ON properties;
CREATE TRIGGER update_properties_updated_at
  BEFORE UPDATE ON properties
  FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_brokers_updated_at ON brokers;
CREATE TRIGGER update_brokers_updated_at
  BEFORE UPDATE ON brokers
  FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_brokerages_updated_at ON brokerages;
CREATE TRIGGER update_brokerages_updated_at
  BEFORE UPDATE ON brokerages
  FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_user_profiles_updated_at ON user_profiles;
CREATE TRIGGER update_user_profiles_updated_at
  BEFORE UPDATE ON user_profiles
  FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_subscriptions_updated_at ON subscriptions;
CREATE TRIGGER update_subscriptions_updated_at
  BEFORE UPDATE ON subscriptions
  FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_saved_properties_updated_at ON saved_properties;
CREATE TRIGGER update_saved_properties_updated_at
  BEFORE UPDATE ON saved_properties
  FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_property_notes_updated_at ON property_notes;
CREATE TRIGGER update_property_notes_updated_at
  BEFORE UPDATE ON property_notes
  FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();