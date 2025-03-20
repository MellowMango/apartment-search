/**
 * API endpoint for admin to synchronize coordinates between properties and property_research
 * 
 * This endpoint:
 * 1. Validates the user is authenticated
 * 2. Runs the SQL fix to ensure proper table relationships
 * 3. Updates property_research modules with coordinates from properties
 * 4. Returns statistics about the operation
 */

import { createClient } from '@supabase/supabase-js';

// Initialize Supabase client
const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL;
const supabaseServiceKey = process.env.SUPABASE_SERVICE_ROLE_KEY;

if (!supabaseUrl || !supabaseServiceKey) {
  console.error('Supabase credentials not configured');
}

const supabase = createClient(supabaseUrl, supabaseServiceKey);

export default async function handler(req, res) {
  // Only allow POST requests
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }
  
  try {
    // Get authorization token
    const authHeader = req.headers.authorization;
    if (!authHeader || !authHeader.startsWith('Bearer ')) {
      return res.status(401).json({ error: 'Unauthorized' });
    }
    
    const token = authHeader.split(' ')[1];
    
    // Verify user is authenticated
    const { data: { user }, error: userError } = await supabase.auth.getUser(token);
    
    if (userError || !user) {
      return res.status(401).json({ error: 'Unauthorized: Invalid token' });
    }
    
    // Process the request
    const { action, limit = 100 } = req.body;
    
    if (action !== 'sync') {
      return res.status(400).json({ error: 'Invalid action' });
    }
    
    // Start timing
    const startTime = Date.now();
    
    // Execute the SQL fix to ensure foreign key relationship is correct
    const sqlFix = `
      -- Alter property_id column to be UUID instead of TEXT if needed
      DO $$ 
      BEGIN
        IF EXISTS (
          SELECT FROM information_schema.columns 
          WHERE table_name = 'property_research' 
          AND column_name = 'property_id' 
          AND data_type != 'uuid'
        ) THEN
          ALTER TABLE public.property_research 
          ALTER COLUMN property_id TYPE UUID USING property_id::uuid;
        END IF;
      END $$;
      
      -- Add foreign key constraint if it doesn't exist
      DO $$ 
      BEGIN
        IF NOT EXISTS (
          SELECT 1 FROM information_schema.table_constraints 
          WHERE constraint_name = 'fk_property_research_property'
        ) THEN
          ALTER TABLE public.property_research
          ADD CONSTRAINT fk_property_research_property
          FOREIGN KEY (property_id) 
          REFERENCES public.properties(id)
          ON DELETE CASCADE;
        END IF;
      END $$;
    `;
    
    await supabase.rpc('execute_sql', { sql: sqlFix });
    
    // Update property_research modules to include coordinates
    const updateSql = `
      UPDATE public.property_research
      SET modules = jsonb_set(
          CASE
              WHEN modules->>'property_details' IS NULL OR modules->'property_details' = 'null'::jsonb THEN
                  jsonb_set(modules, '{property_details}', '{}'::jsonb)
              ELSE
                  modules
          END,
          '{property_details}',
          jsonb_build_object(
              'latitude', (SELECT p.latitude FROM public.properties p WHERE p.id = property_research.property_id),
              'longitude', (SELECT p.longitude FROM public.properties p WHERE p.id = property_research.property_id),
              'address', (SELECT p.address FROM public.properties p WHERE p.id = property_research.property_id),
              'city', (SELECT p.city FROM public.properties p WHERE p.id = property_research.property_id),
              'state', (SELECT p.state FROM public.properties p WHERE p.id = property_research.property_id),
              'zip_code', (SELECT p.zip_code FROM public.properties p WHERE p.id = property_research.property_id)
          )
      )
      WHERE EXISTS (
          SELECT 1 FROM public.properties p 
          WHERE p.id = property_research.property_id
          AND p.latitude IS NOT NULL 
          AND p.longitude IS NOT NULL
          AND p.latitude != 0
          AND p.longitude != 0
      )
      LIMIT $1
    `;
    
    const { count } = await supabase.rpc('execute_sql_with_count', { 
      sql: updateSql,
      params: [limit]
    });
    
    // Calculate duration
    const endTime = Date.now();
    const duration = ((endTime - startTime) / 1000).toFixed(2);
    
    // Return results
    return res.status(200).json({
      success: true,
      updated: count || 0,
      duration,
      message: `Successfully synchronized ${count || 0} properties with coordinates`
    });
  } catch (error) {
    console.error('Error in sync-coordinates API:', error);
    return res.status(500).json({
      success: false,
      error: error.message || 'Internal server error',
      message: 'Failed to synchronize coordinates'
    });
  }
}