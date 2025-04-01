# TypeScript Migration Cleanup Plan

This document outlines the process for safely removing JavaScript files after their TypeScript counterparts have been thoroughly tested and verified.

## Prerequisites

Before beginning the cleanup process:

1. Verify that all TypeScript versions have been tested using the provided test script
2. Ensure all functionality works correctly in the TypeScript implementation
3. Get approval from the team to proceed with cleanup

## Cleanup Process

### Phase 1: Verify TypeScript Implementation

For each component/page:

1. Run the TypeScript version using:
   ```bash
   npm run dev:ts
   ```

2. Complete the test cases from the [test plan](./ts-migration-tests.md)

3. Document any issues and ensure they are resolved before proceeding

### Phase 2: Update Import References

For each migrated file:

1. Search for imports of the JavaScript version:
   ```bash
   grep -r "import.*from ['\"].*components/ComponentName['\"]" --include="*.js" --include="*.jsx" --include="*.ts" --include="*.tsx" ./frontend
   ```

2. Update each import to reference the TypeScript version:
   ```typescript
   // Before
   import Component from '../../components/Component';
   
   // After
   import Component from '../../src/components/Component';
   ```

3. Run the application to verify imports work correctly:
   ```bash
   npm run dev:ts
   ```

### Phase 3: Remove JavaScript Files

For each verified component:

1. Make a backup of the JavaScript file:
   ```bash
   cp frontend/components/Component.js frontend/backup/Component.js.bak
   ```

2. Remove the JavaScript file:
   ```bash
   rm frontend/components/Component.js
   ```

3. Test the application again to ensure it works without the JavaScript file:
   ```bash
   npm run dev:ts
   ```

4. Update the migration progress document

### Phase 4: Final Verification

Once all JavaScript files have been removed:

1. Run a full type check:
   ```bash
   npm run ts:check
   ```

2. Build the application:
   ```bash
   npm run build:ts
   ```

3. Run the application and verify all functionality:
   ```bash
   npm run start
   ```

## Cleanup Order

To minimize disruption, follow this order when removing files:

1. Utility functions
2. Basic UI components
3. Complex components
4. Page components
5. Context providers

## Cleanup Schedule

| Week | Components | Status |
|------|------------|--------|
| 1    | UI Components (Button, Card, etc.) | Pending |
| 1    | Utility Functions | Pending |
| 2    | Layout Components | Pending |
| 2    | Property Components | Pending |
| 3    | Map Components | Pending |
| 3    | Filter Components | Pending |
| 4    | Page Components | Pending |
| 4    | Final Verification | Pending |

## Rollback Plan

If issues arise during cleanup:

1. Restore the JavaScript files from backups:
   ```bash
   cp frontend/backup/Component.js.bak frontend/components/Component.js
   ```

2. Revert import changes:
   ```bash
   git checkout -- [affected files]
   ```

3. Run the application with JavaScript:
   ```bash
   npm run dev
   ```

4. Document the issue and reassess the migration approach

## Post-Cleanup Tasks

After successful cleanup:

1. Update package.json:
   ```diff
   - "dev": "next dev",
   + "dev": "NEXT_PUBLIC_USE_TS=true next dev",
   - "dev:ts": "NEXT_PUBLIC_USE_TS=true next dev -p 3042",
   - "test:ts": "NODE_OPTIONS=--max_old_space_size=4096 NEXT_PUBLIC_USE_TS=true next dev -p 3042",
   - "test:js": "NODE_OPTIONS=--max_old_space_size=4096 NEXT_PUBLIC_USE_TS=false next dev -p 3000"
   ```

2. Remove feature flag system:
   - Remove or simplify `flags.ts`
   - Remove `getMigrationClass` usage from components

3. Update documentation:
   - Mark migration as complete
   - Update README

4. Clean up migration scripts:
   ```bash
   rm scripts/test-ts-migration.sh
   ```

5. Run a final type check and build:
   ```bash
   npm run ts:check
   npm run build
   ```

## Success Criteria

The cleanup is considered successful when:

1. All JavaScript files have been removed
2. The application builds without errors
3. All functionality works correctly
4. TypeScript type checking passes without errors
5. Performance metrics remain the same or improve
6. All documentation has been updated 