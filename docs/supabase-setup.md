# Supabase Setup Guide for Acquire Apartments

This document outlines the setup process for Supabase in the Acquire Apartments (acquire-apartments.com) platform.

## 1. Create Supabase Project

1. Go to [supabase.com](https://supabase.com/) and sign up/login
2. Click "New Project"
3. Enter project details:
   - Name: `acquire-apartments`
   - Database Password: (create a strong password)
   - Region: Select closest to your users (e.g., US East)
4. Click "Create new project"

## 2. Important Credentials

After creating your project, save these credentials securely:

```
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
```

## 3. Database Schema

### Tables to Create

#### Properties Table
```sql
CREATE TABLE properties (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  name TEXT NOT NULL,
  address TEXT NOT NULL,
  city TEXT NOT NULL DEFAULT 'Austin',
  state TEXT NOT NULL DEFAULT 'TX',
  zip_code TEXT,
  latitude NUMERIC,
  longitude NUMERIC,
  price NUMERIC,
  units INTEGER,
  year_built INTEGER,
  square_feet NUMERIC,
  price_per_unit NUMERIC,
  price_per_sqft NUMERIC,
  cap_rate NUMERIC,
  property_type TEXT,
  property_status TEXT DEFAULT 'active',
  description TEXT,
  amenities JSONB,
  images JSONB,
  broker_id UUID,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Enable Row Level Security
ALTER TABLE properties ENABLE ROW LEVEL SECURITY;

-- Create policies
CREATE POLICY "Properties are viewable by everyone" 
  ON properties FOR SELECT USING (true);

CREATE POLICY "Properties are editable by authenticated users" 
  ON properties FOR UPDATE USING (auth.role() = 'authenticated');

CREATE POLICY "Properties are insertable by authenticated users" 
  ON properties FOR INSERT WITH CHECK (auth.role() = 'authenticated');
```

#### Brokers Table
```sql
CREATE TABLE brokers (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  name TEXT NOT NULL,
  company TEXT,
  email TEXT,
  phone TEXT,
  website TEXT,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Enable Row Level Security
ALTER TABLE brokers ENABLE ROW LEVEL SECURITY;

-- Create policies
CREATE POLICY "Brokers are viewable by everyone" 
  ON brokers FOR SELECT USING (true);

CREATE POLICY "Brokers are editable by authenticated users" 
  ON brokers FOR UPDATE USING (auth.role() = 'authenticated');

CREATE POLICY "Brokers are insertable by authenticated users" 
  ON brokers FOR INSERT WITH CHECK (auth.role() = 'authenticated');
```

#### Users Table (Extended Profile)
```sql
CREATE TABLE user_profiles (
  id UUID PRIMARY KEY REFERENCES auth.users,
  full_name TEXT,
  company TEXT,
  subscription_tier TEXT DEFAULT 'free',
  subscription_status TEXT DEFAULT 'active',
  stripe_customer_id TEXT,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Enable Row Level Security
ALTER TABLE user_profiles ENABLE ROW LEVEL SECURITY;

-- Create policies
CREATE POLICY "User profiles are viewable by the user" 
  ON user_profiles FOR SELECT USING (auth.uid() = id);

CREATE POLICY "User profiles are editable by the user" 
  ON user_profiles FOR UPDATE USING (auth.uid() = id);

CREATE POLICY "User profiles are insertable by the user" 
  ON user_profiles FOR INSERT WITH CHECK (auth.uid() = id);
```

## 4. Authentication Setup

1. Go to Authentication → Settings
2. Configure Email Auth:
   - Enable Email confirmations
   - Enable "Secure email change" and "Secure password change"
3. Configure OAuth providers (optional):
   - Google
   - GitHub
   - etc.

## 5. Storage Setup

1. Create buckets for property images:
   - Go to Storage
   - Create a new bucket called `property-images`
   - Set bucket to public

## 6. Environment Variables

Add these to your backend `.env` file:

```
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
```

Add these to your frontend `.env.local` file:

```
NEXT_PUBLIC_SUPABASE_URL=https://your-project-id.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-anon-key
```

## 7. Integration with FastAPI

Install the required packages:

```bash
pip install supabase
```

Basic integration code:

```python
from supabase import create_client
import os

supabase_url = os.environ.get("SUPABASE_URL")
supabase_key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
supabase = create_client(supabase_url, supabase_key)
```

## 8. Integration with Next.js

Install the required packages:

```bash
npm install @supabase/supabase-js
```

Basic integration code:

```javascript
import { createClient } from '@supabase/supabase-js'

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY

export const supabase = createClient(supabaseUrl, supabaseAnonKey)
``` 