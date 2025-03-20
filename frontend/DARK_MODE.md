# Dark Mode Implementation Guide

This document explains how dark mode is implemented in the Austin Multifamily Map application and how to ensure it's maintained across all components and pages.

## Core Implementation

The dark mode implementation uses:

1. **Tailwind CSS** with the `class` strategy for dark mode
2. A React Context for state management
3. localStorage for persistence
4. Media query detection for system preference

## Key Files

- **`src/contexts/ThemeContext.tsx`**: The core context provider and hooks
- **`tailwind.config.js`**: Configuration with `darkMode: 'class'`
- **`src/pages/_app.tsx`**: Global theme provider wrapping
- Various components that use the `useTheme()` hook

## How It Works

1. The `ThemeProvider` in `ThemeContext.tsx` manages theme state and provides:
   - Current theme (`'light'` or `'dark'`)
   - Boolean `isDarkMode` flag
   - `toggleTheme()` function to switch modes
   - `setTheme()` function to set a specific mode

2. When the theme changes, the provider:
   - Toggles the `dark` class on the `<html>` element
   - Saves the preference to localStorage
   - Notifies all consuming components

3. On initial mount, it:
   - Checks localStorage for a saved preference
   - Falls back to system preference if no saved setting
   - Falls back to light mode if neither exists

## Using Dark Mode in Components

```tsx
// Import the hook
import { useTheme } from '../contexts/ThemeContext';

const MyComponent = () => {
  // Get current mode and toggle function
  const { isDarkMode, toggleTheme } = useTheme();
  
  return (
    <div className={`p-4 ${isDarkMode ? 'bg-gray-800 text-white' : 'bg-white text-gray-800'}`}>
      <h1>Component Content</h1>
      
      <button onClick={toggleTheme}>
        Toggle {isDarkMode ? 'Light' : 'Dark'} Mode
      </button>
    </div>
  );
};
```

## Tailwind Dark Mode Classes

Use Tailwind's built-in dark mode variant by prefixing classes with `dark:`:

```jsx
<div className="bg-white text-black dark:bg-gray-800 dark:text-white">
  This element adapts to dark mode automatically
</div>
```

## Best Practices

1. **Always provide both light and dark variants** for:
   - Background colors
   - Text colors
   - Border colors
   - Shadow colors

2. **Use semantic color naming** in custom CSS:
   ```css
   :root {
     --color-background: white;
     --color-text: black;
   }
   
   .dark {
     --color-background: #1a202c;
     --color-text: white;
   }
   ```

3. **Test both modes** whenever adding new components

4. **Use the `useTheme()` hook** rather than checking for dark classes directly

5. **Maintain sufficient contrast** in both modes (at least 4.5:1 ratio)

6. **Consider light/dark image variants** for logos and illustrations

## Dark Mode Color Palette

| Element | Light Mode | Dark Mode |
|---------|------------|-----------|
| Page background | `bg-gray-50` | `dark:bg-gray-900` |
| Component background | `bg-white` | `dark:bg-gray-800` |
| Primary text | `text-gray-900` | `dark:text-white` |
| Secondary text | `text-gray-600` | `dark:text-gray-300` |
| Borders | `border-gray-200` | `dark:border-gray-700` |
| Primary button | `bg-blue-600` | `dark:bg-blue-500` |
| Secondary button | `bg-gray-200` | `dark:bg-gray-700` |
| Inputs | `bg-white border-gray-300` | `dark:bg-gray-700 dark:border-gray-600` |

## System Integration

The dark mode system automatically:
- Respects user preferences from OS settings
- Provides an override toggle
- Remembers user's explicit preference
- Falls back gracefully

## Troubleshooting

1. **Dark mode not working on a component?**
   - Check if the component is under a `ThemeProvider`
   - Verify Tailwind dark classes are correct
   - Check for hardcoded color values that need to be replaced

2. **Flickering on page load?**
   - Add a script to `_document.js` to immediately apply the stored theme

3. **Dark mode not persisting?**
   - Check localStorage permissions
   - Verify theme saving logic in ThemeContext

## Adding Dark Mode to New Components

1. Import the `useTheme` hook from `src/contexts/ThemeContext`
2. Use the `isDarkMode` value for conditional rendering
3. Apply appropriate Tailwind dark mode classes
4. Test in both light and dark modes

Always ensure your components look good and maintain readability in both light and dark modes!