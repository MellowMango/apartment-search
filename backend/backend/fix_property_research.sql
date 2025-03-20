-- Alter property_id column to be UUID instead of TEXT
ALTER TABLE IF EXISTS public.property_research 
    ALTER COLUMN property_id TYPE UUID USING property_id::uuid;

-- Add the foreign key constraint to link properties and property_research
ALTER TABLE IF EXISTS public.property_research
    ADD CONSTRAINT fk_property_research_property
    FOREIGN KEY (property_id) 
    REFERENCES public.properties(id)
    ON DELETE CASCADE;

-- Update property_research modules to include coordinates in the correct format
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
);

-- Create a function to automatically update property_research coordinates when properties are updated
CREATE OR REPLACE FUNCTION update_property_research_coordinates()
RETURNS TRIGGER AS $$
BEGIN
    -- Only update if coordinates changed
    IF (NEW.latitude IS DISTINCT FROM OLD.latitude OR NEW.longitude IS DISTINCT FROM OLD.longitude) AND
       NEW.latitude IS NOT NULL AND NEW.longitude IS NOT NULL AND
       NEW.latitude != 0 AND NEW.longitude != 0 THEN
        
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
                'latitude', NEW.latitude,
                'longitude', NEW.longitude,
                'address', NEW.address,
                'city', NEW.city,
                'state', NEW.state,
                'zip_code', NEW.zip_code
            )
        )
        WHERE property_id = NEW.id;
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create a trigger to automatically update property_research when properties are updated
DROP TRIGGER IF EXISTS update_property_research_on_property_update ON public.properties;
CREATE TRIGGER update_property_research_on_property_update
AFTER UPDATE ON public.properties
FOR EACH ROW
EXECUTE FUNCTION update_property_research_coordinates();