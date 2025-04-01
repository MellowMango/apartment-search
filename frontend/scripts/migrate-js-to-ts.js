#!/usr/bin/env node

/**
 * JavaScript to TypeScript Migration Script
 * 
 * Usage: 
 *   node scripts/migrate-js-to-ts.js <path/to/file.js>
 *   
 * Example:
 *   node scripts/migrate-js-to-ts.js pages/login.js
 */

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

// File to migrate from command line argument
const fileToMigrate = process.argv[2];

if (!fileToMigrate) {
  console.error('Please provide a file path to migrate.');
  process.exit(1);
}

// Source and destination paths
const sourceFile = path.resolve(fileToMigrate);
const destFile = sourceFile.replace(/\.jsx?$/, '.tsx');

// Ensure the source file exists
if (!fs.existsSync(sourceFile)) {
  console.error(`Source file ${sourceFile} does not exist.`);
  process.exit(1);
}

// Check if the destination file already exists
if (fs.existsSync(destFile) && destFile !== sourceFile) {
  console.warn(`Destination file ${destFile} already exists. It will be overwritten.`);
}

// Read the source file
const sourceCode = fs.readFileSync(sourceFile, 'utf8');

// Apply basic transformations
let tsCode = sourceCode
  // Add import React if not present
  .replace(/^((?!import\s+React)[\s\S])*$/, (match) => {
    if (!/import React/.test(match)) {
      return `import React from 'react';\n${match}`;
    }
    return match;
  })
  // Add types to useState
  .replace(/useState\(\s*(['"].*?['"])\s*\)/g, 'useState<string>($1)')
  .replace(/useState\(\s*(\d+)\s*\)/g, 'useState<number>($1)')
  .replace(/useState\(\s*(true|false)\s*\)/g, 'useState<boolean>($1)')
  .replace(/useState\(\s*(\[.*?\])\s*\)/g, 'useState<any[]>($1)')
  .replace(/useState\(\s*\{.*?\}\s*\)/g, 'useState<Record<string, any>>($1)')
  .replace(/useState\(\s*null\s*\)/g, 'useState<null | any>(null)')
  // Add types to function parameters
  .replace(/function\s+(\w+)\s*\(\s*(\w+)\s*\)/g, 'function $1($2: any)')
  .replace(/const\s+(\w+)\s*=\s*\(\s*(\w+)\s*\)\s*=>/g, 'const $1 = ($2: any) =>')
  // Add React.FC to component declarations
  .replace(/function\s+(\w+)\s*\(/g, 'function $1: React.FC<any>(')
  .replace(/const\s+(\w+)\s*=\s*\(\s*\{([^}]*)\}\s*\)\s*=>/g, 'const $1: React.FC<{$2}> = ({$2}) =>');

// Write the TypeScript file
fs.writeFileSync(destFile, tsCode, 'utf8');

console.log(`Migrated ${sourceFile} to ${destFile}`);
console.log('⚠️ Note: This is a basic migration that requires manual review and refinement.');

// Suggest next steps
console.log('\nSuggested next steps:');
console.log('1. Review and refine type definitions in the new file');
console.log('2. Update component props interfaces');
console.log('3. Fix any "any" type annotations with more specific types');
console.log('4. Run "npm run ts:check" to verify TypeScript compilation'); 