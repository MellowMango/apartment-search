# Map Coordinates System Documentation

This document explains the coordinate system used for property mapping in the application, including how coordinates are stored, validated, and displayed.

## Overview

The application uses a dual-source coordinate system:

1. **Primary Source**: Coordinates stored directly in the `properties` table
2. **Enriched Source**: Coordinates stored in the `property_research` table within the `modules.property_details` JSON object

The system prioritizes enriched coordinates from research when available, falling back to the primary source when needed.

## Database Structure

### Properties Table

The main properties table stores basic coordinates:

```sql
CREATE TABLE properties (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  name TEXT,
  address TEXT,
  city TEXT,
  state TEXT,
  zip_code TEXT,
  latitude FLOAT,
  longitude FLOAT,
  /* other fields */
);
```

### Property Research Table

The property_research table stores enriched data including coordinates:

```sql
CREATE TABLE property_research (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  property_id UUID NOT NULL REFERENCES properties(id) ON DELETE CASCADE,
  research_depth TEXT NOT NULL DEFAULT 'standard',
  modules JSONB DEFAULT '{}',
  /* other fields */
);
```

The `modules` JSONB field contains a `property_details` object with coordinates:

```json
{
  "property_details": {
    "latitude": 30.2672,
    "longitude": -97.7431,
    "address": "123 Main St",
    "city": "Austin",
    "state": "TX",
    "zip_code": "78701"
  },
  /* other modules */
}
```

## Foreign Key Relationship

**CRITICAL**: For the map to work correctly, the `property_research` table must have a proper foreign key relationship to the `properties` table. If this relationship is broken or missing, the join operations in the database will fail, and properties won't display correctly on the map.

The SQL to fix this relationship:

```sql
-- Alter property_id column to be UUID instead of TEXT
ALTER TABLE IF EXISTS public.property_research 
    ALTER COLUMN property_id TYPE UUID USING property_id::uuid;

-- Add the foreign key constraint
ALTER TABLE IF EXISTS public.property_research
    ADD CONSTRAINT fk_property_research_property
    FOREIGN KEY (property_id) 
    REFERENCES public.properties(id)
    ON DELETE CASCADE;
```

## Coordinate Validation

The application performs several validation steps to ensure coordinates are valid:

1. **Existence Check**: Both latitude and longitude must exist and be non-null
2. **Type Check**: Coordinates must be numeric
3. **Range Check**: Latitude must be between -90 and 90, longitude between -180 and 180
4. **Zero Check**: Both coordinates cannot be 0, which is often a placeholder
5. **Grid Pattern Detection**: The system detects suspicious "grid patterns" that indicate approximate coordinates

Grid patterns are detected by checking for:
- Low precision coordinates (few decimal places)
- Suspicious patterns like identical lat/lng values
- Common grid values like coordinates ending in .0 or .5
- Sequences of zeros that indicate placeholder values

## Coordinate Flow

### Reading Coordinates

When fetching properties for the map:

1. Query includes a join between `properties` and `property_research`
2. For each property:
   - Check if valid research coordinates exist in `modules.property_details`
   - If so, use these and mark with `_coordinates_from_research = true`
   - Otherwise, use coordinates from the properties table
   - Apply validation to detect suspicious coordinates

### Updating Coordinates

When updating coordinates:

1. Update the `properties` table with new lat/lng values
2. A database trigger fires to propagate changes to the `property_research` table
3. The trigger updates the `modules.property_details` object with the new coordinates

## Geocoding Service

The system includes a `GeocodingService` that provides:

1. **Multi-provider support**: Google Maps, Mapbox, and Nominatim (OpenStreetMap)
2. **Fallback mechanisms**: If one provider fails, the system tries the next
3. **Rate limiting**: To avoid hitting API quotas
4. **Caching**: To minimize duplicate requests
5. **Batch geocoding**: For processing multiple properties at once

The geocoding service is used both in the backend enrichment pipeline and as a fallback in the frontend.

## Frontend Map Display

The `MapComponent.tsx` component:

1. Filters properties to include only those with valid coordinates
2. Prioritizes coordinates from research data
3. Provides visual feedback when geocoding is in progress
4. Creates markers with appropriate styling based on property status
5. Shows empty state feedback when no valid coordinates are available

## Command-Line Tools

Several CLI tools are available for fixing and managing coordinates:

### Backend Fix Script

```bash
python backend/scripts/fix_property_coords.py [--batch-size 50] [--force-update]
```

This script:
- Geocodes properties with missing coordinates
- Updates the `property_research` table with correct formats
- Fixes broken relationships between tables

### Combined Fix Script

```bash
python fix_coordinates.py [--geocode-all] [--batch-size 50]
```

This runs both the SQL fixes and Python geocoding in one command.

## Common Issues and Solutions

### Issue: Properties missing on map

**Potential causes:**
- Missing coordinates in both tables
- Coordinates exist but are in wrong format in `property_research`
- Foreign key relationship broken between tables
- Frontend filtering out suspicious coordinates

**Solutions:**
- Run the fix scripts to repair relationships and update formats
- Use the admin "Sync Coordinates" page
- Check for grid pattern detection flagging valid coordinates

### Issue: Coordinates not transferring to property_research

**Potential causes:**
- Foreign key relationship missing
- Trigger not firing correctly
- JSON structure incorrect in `modules`

**Solution:**
- Run the SQL fix script with the trigger creation

### Issue: Grid pattern detection too strict

The `isGridPattern()` function might be too strict in some cases, especially for properties mapped from plat maps.

**Solution:**
- Consider modifying the grid pattern detection in `geocoding.js` if legitimate coordinates are being filtered out

## Implementation Notes

1. **JSON Structure**: The coordinates must be in `modules.property_details.latitude` and `modules.property_details.longitude` for correct detection.

2. **Foreign Key**: The most common issue is the foreign key relationship being incorrect, preventing proper joining of tables.

3. **Coordinate Priority**: Research coordinates always take precedence over properties table coordinates.

4. **Geocoding Fallbacks**: The system has multiple fallbacks to ensure maximum property display.

## Future Improvements

1. **Coordinate Caching**: Implement client-side caching to reduce API calls

2. **Map Clustering**: Add property clustering for dense areas to improve performance

3. **Viewport-Based Loading**: Only load properties within the current map viewport

4. **Geo-Filtering**: Allow filtering by drawing shapes on the map

5. **Address Validation**: Improve address parsing and validation to increase geocoding success

6. **Batch Geocoding Interface**: Add UI for batch geocoding operations

7. **Coordinate Quality Scoring**: Implement quality scores for coordinates to better prioritize sources