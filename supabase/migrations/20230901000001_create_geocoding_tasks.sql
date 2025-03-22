-- Create a new table for tracking geocoding tasks
CREATE TABLE IF NOT EXISTS "public"."geocoding_tasks" (
  "id" uuid NOT NULL PRIMARY KEY,
  "status" text NOT NULL DEFAULT 'pending',
  "batch_size" int NOT NULL DEFAULT 0,
  "force_refresh" boolean DEFAULT false,
  "start_time" timestamptz NOT NULL,
  "end_time" timestamptz,
  "properties_processed" int,
  "success_count" int,
  "error_count" int,
  "success_rate" numeric,
  "duration_seconds" numeric,
  "error_message" text,
  "created_at" timestamptz NOT NULL DEFAULT now(),
  "updated_at" timestamptz NOT NULL DEFAULT now()
);

-- Add index on status for faster queries
CREATE INDEX IF NOT EXISTS "geocoding_tasks_status_idx" ON "public"."geocoding_tasks" ("status");

-- Enable RLS (Row Level Security)
ALTER TABLE "public"."geocoding_tasks" ENABLE ROW LEVEL SECURITY;

-- Create a trigger to automatically update the updated_at field
CREATE OR REPLACE FUNCTION "public"."handle_updated_at"()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = now();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply the trigger to the geocoding_tasks table
CREATE TRIGGER "set_geocoding_tasks_updated_at"
BEFORE UPDATE ON "public"."geocoding_tasks"
FOR EACH ROW
EXECUTE FUNCTION "public"."handle_updated_at"();

-- Create a policy that allows only authenticated users to select
CREATE POLICY "Allow read access for authenticated users"
ON "public"."geocoding_tasks"
FOR SELECT
USING (auth.role() = 'authenticated');

-- Add a column to properties table to track when a property was last geocoded
ALTER TABLE "public"."properties"
ADD COLUMN IF NOT EXISTS "geocoded_at" timestamptz; 