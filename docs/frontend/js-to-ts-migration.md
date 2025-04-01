# JavaScript to TypeScript Migration Plan

## Current State Analysis

### File Structure Issues
- `/frontend/pages/*.js` - Currently active JavaScript files
- `/frontend/src/pages/*.tsx` - Partially implemented TypeScript versions
- Potential routing conflicts due to duplicate page definitions

### Key Files to Migrate
1. **Map Page**
   - Current: `/frontend/pages/map.js` (55KB)
   - Target: `/frontend/src/pages/map.tsx` (53KB)
   
2. **Index Page**
   - Current: `/frontend/pages/index.js` (21KB)
   - Target: `/frontend/src/pages/index.tsx` (11KB)

3. **Other Pages**
   - Login/Signup
   - Reset/Update Password
   - Admin pages
   - API routes

## Migration Strategy

### Phase 1: Setup and Preparation (1-2 days)

1. **TypeScript Configuration**
   ```bash
   # Verify TypeScript setup
   npm install --save-dev typescript @types/react @types/node
   
   # Generate tsconfig.json if needed
   npx tsc --init
   ```

2. **Update Next.js Configuration**
   ```javascript
   // next.config.js
   module.exports = {
     pageExtensions: ['tsx', 'ts'],  // Prefer TypeScript files
     webpack: (config, { buildId, dev, isServer, defaultLoaders, webpack }) => {
       // Custom webpack config if needed
       return config
     },
   }
   ```

3. **Create Type Definitions**
   ```typescript
   // frontend/src/types/property.ts
   export interface Property {
     id: string;
     name: string;
     address: string;
     city?: string;
     state?: string;
     zip?: string;
     units?: number;
     num_units?: number;
     price?: number;
     price_per_unit?: number;
     year_built?: number;
     latitude?: number;
     longitude?: number;
     status?: string;
     property_status?: string;
     created_at?: string;
     updated_at?: string;
     broker?: string;
     image_url?: string;
     _geocoded?: boolean;
     _geocoding_failed?: boolean;
     _coordinates_missing?: boolean;
     _needs_geocoding?: boolean;
     _is_grid_pattern?: boolean;
     _is_test_property?: boolean;
     _data_quality_issues?: string[];
     _data_cleaned?: boolean;
     _cleaning_notes?: string;
     _data_enriched?: boolean;
     _enrichment_notes?: string;
   }
   ```

### Phase 2: Component Migration (2-3 days)

1. **Create TypeScript Versions of Components**
   - Start with shared components
   - Add proper type definitions
   - Test components in isolation

2. **Migration Order**
   ```
   1. Basic UI components (buttons, inputs)
   2. Layout components
   3. Map-related components
   4. Complex feature components
   ```

3. **Example Component Migration**
   ```typescript
   // Before (JavaScript)
   export const MapComponent = ({ properties, selectedProperty }) => {
     // ...
   }

   // After (TypeScript)
   interface MapComponentProps {
     properties: Property[];
     selectedProperty: Property | null;
     setSelectedProperty: (property: Property | null) => void;
     onBoundsChange?: (bounds: MapBounds) => void;
   }

   export const MapComponent: React.FC<MapComponentProps> = ({
     properties,
     selectedProperty,
     setSelectedProperty,
     onBoundsChange
   }) => {
     // ...
   }
   ```

### Phase 3: Page Migration (2-3 days)

1. **Testing Environment Setup**
   ```bash
   # Add test script to package.json
   "scripts": {
     "test:ts": "NODE_OPTIONS=--max_old_space_size=4096 next dev -p 3001"
   }
   ```

2. **Migration Process for Each Page**
   a. Create TypeScript version
   b. Add type definitions
   c. Test in parallel with JS version
   d. Switch over when stable

3. **Feature Flags for Testing**
   ```typescript
   // frontend/src/config/flags.ts
   export const FLAGS = {
     USE_TYPESCRIPT_PAGES: process.env.NEXT_PUBLIC_USE_TS === 'true'
   }
   ```

### Phase 4: Testing and Validation (2-3 days)

1. **Parallel Testing Strategy**
   - Run both JS and TS versions
   - Compare functionality
   - Document differences
   - Fix issues

2. **Type Coverage Goals**
   - 90% type coverage for new code
   - Minimum 70% for migrated code
   - No `any` types in critical paths

3. **Performance Benchmarks**
   - Page load times
   - Memory usage
   - Bundle sizes

## Running TypeScript Version

To test the TypeScript version while keeping the JavaScript version as fallback:

1. **Development Testing**
   ```bash
   # Run TypeScript version on port 3001
   npm run test:ts

   # Run current JavaScript version on port 3000
   npm run dev
   ```

2. **Environment Variables**
   ```env
   # .env.development
   NEXT_PUBLIC_USE_TS=true
   ```

## Rollback Plan

1. **Quick Rollback**
   ```bash
   # Revert to JavaScript version
   git checkout main -- frontend/pages/
   npm run dev
   ```

2. **Partial Rollback**
   - Keep TypeScript definitions
   - Revert specific pages
   - Maintain dual support temporarily

## Migration Progress Tracking

Create a progress tracking file at `/docs/ts-migration-progress.md`:

```markdown
# TypeScript Migration Progress

## Components
- [ ] Layout
- [ ] Navigation
- [ ] Map
- [ ] Property List
- [ ] Filters
- [ ] Search

## Pages
- [ ] Map Page
- [ ] Index Page
- [ ] Login/Signup
- [ ] Admin Pages

## Types
- [x] Property Interface
- [ ] User Interface
- [ ] API Response Types
- [ ] Map Types
```

## Success Criteria

1. **Functionality**
   - All features working in TypeScript
   - No regression in user experience
   - All tests passing

2. **Type Safety**
   - No `any` types in critical paths
   - Comprehensive interface definitions
   - Proper error handling

3. **Performance**
   - Equal or better load times
   - No increase in bundle size
   - Smooth map interactions

## Timeline

Total Estimated Time: 7-11 days

1. Setup and Preparation: 1-2 days
2. Component Migration: 2-3 days
3. Page Migration: 2-3 days
4. Testing and Validation: 2-3 days

## Next Steps

1. Begin with setup and preparation phase
2. Create type definitions for core interfaces
3. Start with small, isolated components
4. Test TypeScript version in parallel
5. Document all issues and solutions

## Notes

- Keep both versions running until migration is complete
- Use feature flags to toggle between versions
- Maintain detailed migration logs
- Regular testing throughout the process
- Consider breaking changes in TypeScript versions 