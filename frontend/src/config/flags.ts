/**
 * Feature flags to control migration features
 */
export const FLAGS = {
  // Controls whether to use TypeScript pages or fall back to JavaScript
  USE_TYPESCRIPT_PAGES: process.env.NEXT_PUBLIC_USE_TS === 'true',
  
  // Controls visual indicators during migration (adds indicators to migrated pages)
  SHOW_MIGRATION_INDICATORS: process.env.NODE_ENV === 'development',
  
  // Enables any experimental features during migration
  ENABLE_EXPERIMENTAL: false,
}

/**
 * Helper to check if a feature flag is enabled
 */
export function isFeatureEnabled(flagName: keyof typeof FLAGS): boolean {
  return FLAGS[flagName] === true;
}

/**
 * Helper to add migration indicator class if enabled
 */
export function getMigrationClass(componentName: string): string {
  return isFeatureEnabled('SHOW_MIGRATION_INDICATORS') 
    ? `ts-migrated ts-${componentName.toLowerCase()}` 
    : '';
} 