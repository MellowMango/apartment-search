# TypeScript Migration Guide

This guide provides detailed instructions for continuing and completing the migration from JavaScript to TypeScript in the Acquire Apartments application.

## Current Status

As of now, approximately 85% of the codebase has been migrated to TypeScript. The migration uses a feature flag system (`USE_TYPESCRIPT_PAGES`) to allow for graceful transition between JavaScript and TypeScript implementations.

For detailed progress information, see the [migration progress document](./ts-migration-progress.md).

## Development Environment

### Prerequisites

- Node.js 16+ and npm
- TypeScript 5.2+
- Next.js 14+

### Setup

Ensure all dependencies are installed:

```bash
cd frontend
npm install
```

### Running the Application

You can run either the JavaScript or TypeScript implementation:

```bash
# JavaScript version (port 3000)
npm run dev

# TypeScript version (port 3042)
npm run dev:ts
```

### Testing Both Implementations

To test both implementations side by side:

```bash
# From project root
./scripts/test-ts-migration.sh
```

This script:
- Launches both versions in separate terminals using tmux
- Opens browser windows to each version
- Helps identify discrepancies between implementations

If you don't have tmux installed, the script provides instructions for manual setup.

## Migration Workflow

### 1. Identifying Files for Migration

Files needing migration are located in:
- `/frontend/pages/*.js` - Active JavaScript files
- `/frontend/components/*.js` - JavaScript components

TypeScript versions should be created in:
- `/frontend/src/pages/*.tsx` - TypeScript pages
- `/frontend/src/components/*.tsx` - TypeScript components

### 2. Creating TypeScript Versions

For each JavaScript file:

1. Create the corresponding TypeScript file
2. Add proper type definitions
3. Use the feature flag system to enable testing
4. Apply the migration class indicator

Example:

```typescript
import { getMigrationClass } from '../config/flags';

interface ComponentProps {
  // Define props here
}

const MyComponent: React.FC<ComponentProps> = (props) => {
  return (
    <div className={getMigrationClass('MyComponent')}>
      {/* Component content */}
    </div>
  );
};
```

### 3. Testing

For each migrated file:

1. Run both versions using the test script
2. Compare functionality and appearance
3. Verify all features work correctly
4. Check for type errors
5. Document any issues

Follow the test cases in the [test plan document](./ts-migration-tests.md).

### 4. Cleanup Process

Once a component has been thoroughly tested:

1. Update imports in other files to reference the TypeScript version
2. Remove the JavaScript version
3. Update the migration progress document

## Type Definitions

### Core Types

Key type definitions are located in:

- `/frontend/src/types/property.ts` - Property interface
- `/frontend/src/types/user.ts` - User interface

### Using Types

Import types in your components:

```typescript
import { Property } from '../types/property';
import { User } from '../types/user';

interface ComponentProps {
  property: Property;
  user?: User;
}
```

## Feature Flag System

The migration uses a feature flag system to control which implementation is used.

### Configuration

Feature flags are defined in `/frontend/src/config/flags.ts`:

```typescript
export const FLAGS = {
  USE_TYPESCRIPT_PAGES: process.env.NEXT_PUBLIC_USE_TS === 'true',
  SHOW_MIGRATION_INDICATORS: process.env.NODE_ENV === 'development'
}
```

### Usage

To apply visual indicators during testing:

```typescript
import { getMigrationClass } from '../config/flags';

<div className={getMigrationClass('ComponentName')}>
  {/* Component content */}
</div>
```

### Environment Variables

Control which implementation is used with:

```
NEXT_PUBLIC_USE_TS=true|false
```

## Migration Completion Checklist

Once all files have been migrated and tested:

1. Remove feature flag usage from components
2. Update import paths to use only TypeScript files
3. Remove JavaScript versions
4. Update tsconfig.json to include all files
5. Remove migration-specific scripts
6. Update documentation

## Troubleshooting

### Common Issues

#### Type Errors

If you encounter type errors:

1. Check the property/parameter types
2. Add optional chaining for nullable values
3. Use proper type guards

Example:
```typescript
// Before
const name = property.name;

// After
const name = property?.name || 'Unnamed Property';
```

#### Component Compatibility

If a component behaves differently:

1. Compare props between versions
2. Check effect dependencies
3. Verify state initialization

#### Import Errors

If imports fail:

1. Check path aliases in tsconfig.json
2. Verify file exists in the expected location
3. Update import statements to use correct paths

## Additional Resources

- [TypeScript Documentation](https://www.typescriptlang.org/docs/)
- [Next.js TypeScript Documentation](https://nextjs.org/docs/basic-features/typescript)
- [React TypeScript Cheatsheet](https://react-typescript-cheatsheet.netlify.app/) 