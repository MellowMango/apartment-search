-- Check Schema Script for Acquire Apartments
-- This script verifies that all tables, columns, constraints, policies, and triggers are correctly set up
-- Run this in the Supabase SQL editor to check your schema

-- 1. List all tables in the public schema
SELECT 'Tables in public schema:' as info;
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public'
ORDER BY table_name;

-- 2. Check primary keys
SELECT '=== Primary Keys ===' as info;
SELECT
    tc.table_name, 
    kcu.column_name
FROM 
    information_schema.table_constraints AS tc 
    JOIN information_schema.key_column_usage AS kcu
      ON tc.constraint_name = kcu.constraint_name
      AND tc.table_schema = kcu.table_schema
WHERE tc.constraint_type = 'PRIMARY KEY' AND tc.table_schema = 'public'
ORDER BY tc.table_name;

-- 3. Check foreign key constraints
SELECT '=== Foreign Key Constraints ===' as info;
SELECT
    tc.table_name, 
    kcu.column_name, 
    ccu.table_name AS foreign_table_name,
    ccu.column_name AS foreign_column_name 
FROM 
    information_schema.table_constraints AS tc 
    JOIN information_schema.key_column_usage AS kcu
      ON tc.constraint_name = kcu.constraint_name
      AND tc.table_schema = kcu.table_schema
    JOIN information_schema.constraint_column_usage AS ccu
      ON ccu.constraint_name = tc.constraint_name
      AND ccu.table_schema = tc.table_schema
WHERE tc.constraint_type = 'FOREIGN KEY' AND tc.table_schema = 'public'
ORDER BY tc.table_name, kcu.column_name;

-- 4. Check RLS policies
SELECT '=== Row Level Security Policies ===' as info;
SELECT
    tablename,
    policyname,
    cmd,
    roles
FROM
    pg_policies
WHERE
    schemaname = 'public'
ORDER BY
    tablename, policyname;

-- 5. Check triggers
SELECT '=== Triggers ===' as info;
SELECT
    event_object_table,
    trigger_name,
    event_manipulation,
    action_statement
FROM
    information_schema.triggers
WHERE
    trigger_schema = 'public'
ORDER BY
    event_object_table, trigger_name;

-- 6. Check if update_updated_at_column function exists
SELECT '=== Check update_updated_at_column Function ===' as info;
SELECT EXISTS(
    SELECT 1 FROM pg_proc WHERE proname = 'update_updated_at_column'
) as function_exists;

-- 7. Count records in each table
SELECT '=== Record Counts ===' as info;
SELECT 'properties' as table_name, COUNT(*) as record_count FROM properties
UNION ALL
SELECT 'brokerages' as table_name, COUNT(*) as record_count FROM brokerages
UNION ALL
SELECT 'brokers' as table_name, COUNT(*) as record_count FROM brokers
UNION ALL
SELECT 'user_profiles' as table_name, COUNT(*) as record_count FROM user_profiles
UNION ALL
SELECT 'subscriptions' as table_name, COUNT(*) as record_count FROM subscriptions
UNION ALL
SELECT 'saved_properties' as table_name, COUNT(*) as record_count FROM saved_properties
UNION ALL
SELECT 'property_notes' as table_name, COUNT(*) as record_count FROM property_notes
ORDER BY table_name; 