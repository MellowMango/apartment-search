# TypeScript Migration Plan

This document outlines our approach to migrating the Acquire Apartments frontend from JavaScript to TypeScript.

## Completed Steps

1. **Infrastructure Setup**
   - ✅ Updated `tsconfig.json` with stricter type checking and path aliases
   - ✅ Added type declarations for UI components
   - ✅ Created core type definitions for users and auth
   - ✅ Added feature flags for controlled migration

2. **Initial Component Migration**
   - ✅ Migrated AuthContext to TypeScript
   - ✅ Migrated login page as proof of concept

## Migration Process

For each file to be migrated, follow these steps:

1. **Preparation**
   - Create TypeScript types for any data structures used in the file
   - Identify component props and state that need typing

2. **Migration**
   - Use the migration script as a starting point: `npm run migrate path/to/file.js`
   - Add proper types to replace any `any` types
   - Add interface definitions for component props
   - Ensure event handlers have proper type annotations
   - Fix any errors or warnings

3. **Testing**
   - Run TypeScript type checking: `npm run ts:check`
   - Test the component in the TypeScript environment: `npm run dev:ts`
   - Verify feature parity with the JavaScript version

4. **Documentation**
   - Update the migration progress document
   - Add JSDoc comments for complex functions or components

## Migration Strategy

We're following a phased approach to minimize disruption:

### Phase 1: Core Infrastructure (Completed)
- Setup TypeScript configuration
- Define shared types
- Create utility for dual-mode operation

### Phase 2: Auth Pages (In Progress)
- Login page (completed)
- Signup page
- Password reset/update pages

### Phase 3: Shared Components
- UI components
- Layout components
- Navigation components

### Phase 4: Main Pages
- Index page
- Map page
- Details pages

### Phase 5: Testing & Cleanup
- End-to-end testing
- Code review and refinement
- Remove JavaScript versions

## Dual-Mode Operation

During the migration, we're supporting both JavaScript and TypeScript versions:

- JavaScript pages run on port 3000: `npm run dev`
- TypeScript pages run on port 3001: `npm run dev:ts`

The feature flag `NEXT_PUBLIC_USE_TS=true` controls which version is used.

## Type Definitions

Key type definitions are located in:
- `/frontend/src/types/` - Core type definitions
- `/frontend/components/ui/index.d.ts` - UI component type declarations

## Resources

- [TypeScript Migration Guide](https://www.typescriptlang.org/docs/handbook/migrating-from-javascript.html)
- [React TypeScript Cheatsheet](https://react-typescript-cheatsheet.netlify.app/)
- [Next.js TypeScript Documentation](https://nextjs.org/docs/basic-features/typescript)

## Rollback Plan

If issues arise, we can easily revert to the JavaScript version:

1. Set `NEXT_PUBLIC_USE_TS=false` (default)
2. Ensure original JavaScript files remain intact until migration is complete
3. To completely revert, restore files from version control: `git checkout main -- frontend/pages/`

## Next Steps

1. Complete migration of remaining auth pages
2. Migrate shared components
3. Update progress tracking document 