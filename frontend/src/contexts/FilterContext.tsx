/**
 * FilterContext.tsx
 * Manages property filtering state across the application
 * 
 * This context provides:
 * - Current filter state (search terms, price range, unit count, etc.)
 * - Functions to update filters
 * - Ability to save and restore filter sets
 * 
 * Usage:
 * 1. Wrap components that need filter state with FilterProvider
 * 2. Use useFilter() hook to access filter state and update functions
 * 3. When an update function is called, all subscribers will be notified
 */

import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { PropertySearchParams } from '../types/property';

interface FilterContextType {
  filters: PropertySearchParams;
  updateFilter: (key: string, value: any) => void;
  updateFilters: (newFilters: Partial<PropertySearchParams>) => void;
  clearFilters: () => void;
  saveFilter: (name: string) => void;
  loadFilter: (name: string) => void;
  savedFilters: SavedFilter[];
}

interface SavedFilter {
  name: string;
  filters: PropertySearchParams;
  timestamp: number;
}

// Default filter values
const defaultFilters: PropertySearchParams = {
  search: '',
  status: '',
  min_price: undefined,
  max_price: undefined,
  min_units: undefined,
  max_units: undefined,
  city: '',
  state: '',
  zip: '',
  year_built_min: undefined,
  year_built_max: undefined,
  cap_rate_min: undefined,
  cap_rate_max: undefined,
  sort_by: 'created_at',
  sort_dir: 'desc',
  page: 1,
  limit: 1000, // Increased to 1000 to show more properties on the map
};

const FilterContext = createContext<FilterContextType | undefined>(undefined);

interface FilterProviderProps {
  children: ReactNode;
  initialFilters?: Partial<PropertySearchParams>;
}

export const FilterProvider: React.FC<FilterProviderProps> = ({ 
  children, 
  initialFilters = {} 
}) => {
  // Initialize with default filters and any provided initial values
  const [filters, setFilters] = useState<PropertySearchParams>({
    ...defaultFilters,
    ...initialFilters,
  });
  
  // Saved filters in localStorage
  const [savedFilters, setSavedFilters] = useState<SavedFilter[]>([]);
  
  // Load saved filters from localStorage on mount
  useEffect(() => {
    if (typeof window !== 'undefined') {
      const stored = localStorage.getItem('savedFilters');
      if (stored) {
        try {
          setSavedFilters(JSON.parse(stored));
        } catch (e) {
          console.error('Error loading saved filters:', e);
        }
      }
    }
  }, []);
  
  // Update a single filter value
  const updateFilter = (key: string, value: any) => {
    setFilters(prev => {
      // Reset to page 1 whenever a filter changes
      if (key !== 'page') {
        return { ...prev, [key]: value, page: 1 };
      }
      return { ...prev, [key]: value };
    });
  };
  
  // Update multiple filters at once
  const updateFilters = (newFilters: Partial<PropertySearchParams>) => {
    setFilters(prev => {
      // Reset to page 1 if any filter other than page is changing
      const resetPage = Object.keys(newFilters).some(key => key !== 'page');
      return { 
        ...prev, 
        ...newFilters,
        ...(resetPage ? { page: 1 } : {})
      };
    });
  };
  
  // Reset filters to default values
  const clearFilters = () => {
    setFilters(defaultFilters);
  };
  
  // Save current filter set to localStorage
  const saveFilter = (name: string) => {
    const newSavedFilter: SavedFilter = {
      name,
      filters: { ...filters },
      timestamp: Date.now(),
    };
    
    const updated = [...savedFilters, newSavedFilter];
    setSavedFilters(updated);
    
    if (typeof window !== 'undefined') {
      localStorage.setItem('savedFilters', JSON.stringify(updated));
    }
  };
  
  // Load a saved filter set
  const loadFilter = (name: string) => {
    const savedFilter = savedFilters.find(f => f.name === name);
    if (savedFilter) {
      setFilters(savedFilter.filters);
    }
  };
  
  return (
    <FilterContext.Provider value={{
      filters,
      updateFilter,
      updateFilters,
      clearFilters,
      saveFilter,
      loadFilter,
      savedFilters,
    }}>
      {children}
    </FilterContext.Provider>
  );
};

// Custom hook to use the filter context
export const useFilter = (): FilterContextType => {
  const context = useContext(FilterContext);
  
  if (context === undefined) {
    throw new Error('useFilter must be used within a FilterProvider');
  }
  
  return context;
};

export default FilterContext;