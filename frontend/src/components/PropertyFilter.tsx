/**
 * PropertyFilter.tsx
 * Component for filtering properties on the map page
 * 
 * Features:
 * - Search by address or name
 * - Filter by price range
 * - Filter by number of units
 * - Filter by year built
 * - Filter by property status
 * - Save and load filter sets
 */

import React, { useState } from 'react';
import { useFilter } from '../contexts/FilterContext';
import { useTheme } from '../contexts/ThemeContext';

interface PropertyFilterProps {
  onApplyFilter: () => void;
  className?: string;
}

const PropertyFilter: React.FC<PropertyFilterProps> = ({ 
  onApplyFilter,
  className = '' 
}) => {
  const { filters, updateFilter, updateFilters, clearFilters, saveFilter, loadFilter, savedFilters } = useFilter();
  const { isDarkMode } = useTheme();
  
  // Local state for filter inputs before applying
  const [searchInput, setSearchInput] = useState(filters.search || '');
  const [minPrice, setMinPrice] = useState<string>(filters.min_price?.toString() || '');
  const [maxPrice, setMaxPrice] = useState<string>(filters.max_price?.toString() || '');
  const [minUnits, setMinUnits] = useState<string>(filters.min_units?.toString() || '');
  const [maxUnits, setMaxUnits] = useState<string>(filters.max_units?.toString() || '');
  const [minYear, setMinYear] = useState<string>(filters.year_built_min?.toString() || '');
  const [maxYear, setMaxYear] = useState<string>(filters.year_built_max?.toString() || '');
  const [status, setStatus] = useState<string>(filters.status || '');
  const [saveFilterName, setSaveFilterName] = useState('');
  const [isAdvancedOpen, setIsAdvancedOpen] = useState(false);
  const [showSaveFilter, setShowSaveFilter] = useState(false);
  
  // Apply current filter values
  const handleApplyFilter = () => {
    updateFilters({
      search: searchInput,
      min_price: minPrice ? parseFloat(minPrice) : undefined,
      max_price: maxPrice ? parseFloat(maxPrice) : undefined,
      min_units: minUnits ? parseInt(minUnits) : undefined,
      max_units: maxUnits ? parseInt(maxUnits) : undefined,
      year_built_min: minYear ? parseInt(minYear) : undefined,
      year_built_max: maxYear ? parseInt(maxYear) : undefined,
      status: status || undefined,
    });
    
    onApplyFilter();
  };
  
  // Reset form and clear filters
  const handleClearFilters = () => {
    setSearchInput('');
    setMinPrice('');
    setMaxPrice('');
    setMinUnits('');
    setMaxUnits('');
    setMinYear('');
    setMaxYear('');
    setStatus('');
    
    clearFilters();
    onApplyFilter();
  };
  
  // Save current filter set
  const handleSaveFilter = () => {
    if (saveFilterName.trim()) {
      saveFilter(saveFilterName);
      setSaveFilterName('');
      setShowSaveFilter(false);
    }
  };
  
  // Load a saved filter set
  const handleLoadFilter = (name: string) => {
    loadFilter(name);
    
    // Find the saved filter
    const saved = savedFilters.find(f => f.name === name);
    if (saved) {
      // Update local state
      setSearchInput(saved.filters.search || '');
      setMinPrice(saved.filters.min_price?.toString() || '');
      setMaxPrice(saved.filters.max_price?.toString() || '');
      setMinUnits(saved.filters.min_units?.toString() || '');
      setMaxUnits(saved.filters.max_units?.toString() || '');
      setMinYear(saved.filters.year_built_min?.toString() || '');
      setMaxYear(saved.filters.year_built_max?.toString() || '');
      setStatus(saved.filters.status || '');
      
      onApplyFilter();
    }
  };
  
  // Base styles for the filter container
  const containerStyles = `p-4 rounded-lg shadow-md ${isDarkMode ? 'bg-gray-800 text-white' : 'bg-white'} ${className}`;
  
  return (
    <div className={containerStyles}>
      <h2 className={`text-lg font-semibold mb-4 ${isDarkMode ? 'text-gray-100' : 'text-gray-800'}`}>Filter Properties</h2>
      
      {/* Search input */}
      <div className="mb-4">
        <label htmlFor="search" className={`block text-sm font-medium mb-1 ${isDarkMode ? 'text-gray-300' : 'text-gray-600'}`}>
          Search
        </label>
        <div className="relative">
          <input
            type="text"
            id="search"
            placeholder="Address, property name..."
            value={searchInput}
            onChange={(e) => setSearchInput(e.target.value)}
            className={`block w-full px-3 py-2 border rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 ${
              isDarkMode ? 'bg-gray-700 border-gray-600 text-white placeholder-gray-400' : 'bg-white border-gray-300 text-gray-900 placeholder-gray-500'
            }`}
          />
          {searchInput && (
            <button
              type="button"
              onClick={() => setSearchInput('')}
              className="absolute inset-y-0 right-0 pr-3 flex items-center"
            >
              <svg xmlns="http://www.w3.org/2000/svg" className={`h-4 w-4 ${isDarkMode ? 'text-gray-400' : 'text-gray-500'}`} fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          )}
        </div>
      </div>
      
      {/* Status filter */}
      <div className="mb-4">
        <label htmlFor="status" className={`block text-sm font-medium mb-1 ${isDarkMode ? 'text-gray-300' : 'text-gray-600'}`}>
          Status
        </label>
        <select
          id="status"
          value={status}
          onChange={(e) => setStatus(e.target.value)}
          className={`block w-full px-3 py-2 border rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 ${
            isDarkMode ? 'bg-gray-700 border-gray-600 text-white' : 'bg-white border-gray-300 text-gray-900'
          }`}
        >
          <option value="">Any Status</option>
          <option value="Available">Available</option>
          <option value="For Sale">For Sale</option>
          <option value="Under Contract">Under Contract</option>
          <option value="Sold">Sold</option>
          <option value="Actively Marketed">Actively Marketed</option>
        </select>
      </div>
      
      {/* Toggle for Advanced Filters */}
      <button
        type="button"
        onClick={() => setIsAdvancedOpen(!isAdvancedOpen)}
        className={`flex items-center text-sm font-medium mb-4 ${isDarkMode ? 'text-blue-400' : 'text-blue-600'}`}
      >
        {isAdvancedOpen ? 'Hide Advanced Filters' : 'Show Advanced Filters'}
        <svg 
          xmlns="http://www.w3.org/2000/svg" 
          className={`ml-1 h-4 w-4 transform transition-transform ${isAdvancedOpen ? 'rotate-180' : ''}`}
          fill="none" 
          viewBox="0 0 24 24" 
          stroke="currentColor"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </button>
      
      {/* Advanced Filters */}
      {isAdvancedOpen && (
        <div className="space-y-4 mb-4 border-t border-b py-4">
          {/* Price Range */}
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label htmlFor="minPrice" className={`block text-sm font-medium mb-1 ${isDarkMode ? 'text-gray-300' : 'text-gray-600'}`}>
                Min Price ($)
              </label>
              <input
                type="number"
                id="minPrice"
                placeholder="Min"
                value={minPrice}
                onChange={(e) => setMinPrice(e.target.value)}
                className={`block w-full px-3 py-2 border rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 ${
                  isDarkMode ? 'bg-gray-700 border-gray-600 text-white placeholder-gray-400' : 'bg-white border-gray-300 text-gray-900 placeholder-gray-500'
                }`}
              />
            </div>
            <div>
              <label htmlFor="maxPrice" className={`block text-sm font-medium mb-1 ${isDarkMode ? 'text-gray-300' : 'text-gray-600'}`}>
                Max Price ($)
              </label>
              <input
                type="number"
                id="maxPrice"
                placeholder="Max"
                value={maxPrice}
                onChange={(e) => setMaxPrice(e.target.value)}
                className={`block w-full px-3 py-2 border rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 ${
                  isDarkMode ? 'bg-gray-700 border-gray-600 text-white placeholder-gray-400' : 'bg-white border-gray-300 text-gray-900 placeholder-gray-500'
                }`}
              />
            </div>
          </div>
          
          {/* Units Range */}
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label htmlFor="minUnits" className={`block text-sm font-medium mb-1 ${isDarkMode ? 'text-gray-300' : 'text-gray-600'}`}>
                Min Units
              </label>
              <input
                type="number"
                id="minUnits"
                placeholder="Min"
                value={minUnits}
                onChange={(e) => setMinUnits(e.target.value)}
                className={`block w-full px-3 py-2 border rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 ${
                  isDarkMode ? 'bg-gray-700 border-gray-600 text-white placeholder-gray-400' : 'bg-white border-gray-300 text-gray-900 placeholder-gray-500'
                }`}
              />
            </div>
            <div>
              <label htmlFor="maxUnits" className={`block text-sm font-medium mb-1 ${isDarkMode ? 'text-gray-300' : 'text-gray-600'}`}>
                Max Units
              </label>
              <input
                type="number"
                id="maxUnits"
                placeholder="Max"
                value={maxUnits}
                onChange={(e) => setMaxUnits(e.target.value)}
                className={`block w-full px-3 py-2 border rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 ${
                  isDarkMode ? 'bg-gray-700 border-gray-600 text-white placeholder-gray-400' : 'bg-white border-gray-300 text-gray-900 placeholder-gray-500'
                }`}
              />
            </div>
          </div>
          
          {/* Year Built Range */}
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label htmlFor="minYear" className={`block text-sm font-medium mb-1 ${isDarkMode ? 'text-gray-300' : 'text-gray-600'}`}>
                Min Year Built
              </label>
              <input
                type="number"
                id="minYear"
                placeholder="Min"
                value={minYear}
                onChange={(e) => setMinYear(e.target.value)}
                className={`block w-full px-3 py-2 border rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 ${
                  isDarkMode ? 'bg-gray-700 border-gray-600 text-white placeholder-gray-400' : 'bg-white border-gray-300 text-gray-900 placeholder-gray-500'
                }`}
              />
            </div>
            <div>
              <label htmlFor="maxYear" className={`block text-sm font-medium mb-1 ${isDarkMode ? 'text-gray-300' : 'text-gray-600'}`}>
                Max Year Built
              </label>
              <input
                type="number"
                id="maxYear"
                placeholder="Max"
                value={maxYear}
                onChange={(e) => setMaxYear(e.target.value)}
                className={`block w-full px-3 py-2 border rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 ${
                  isDarkMode ? 'bg-gray-700 border-gray-600 text-white placeholder-gray-400' : 'bg-white border-gray-300 text-gray-900 placeholder-gray-500'
                }`}
              />
            </div>
          </div>
        </div>
      )}
      
      {/* Filter action buttons */}
      <div className="flex space-x-2">
        <button
          type="button"
          onClick={handleApplyFilter}
          className="flex-1 px-4 py-2 bg-blue-600 border border-transparent rounded-md shadow-sm text-sm font-medium text-white hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
        >
          Apply Filters
        </button>
        <button
          type="button"
          onClick={handleClearFilters}
          className={`px-4 py-2 border rounded-md shadow-sm text-sm font-medium ${
            isDarkMode
              ? 'border-gray-600 text-gray-300 hover:bg-gray-700'
              : 'border-gray-300 text-gray-700 hover:bg-gray-50'
          }`}
        >
          Clear
        </button>
      </div>
      
      {/* Saved Filters */}
      {savedFilters.length > 0 && (
        <div className="mt-6">
          <div className="flex items-center justify-between">
            <h3 className={`text-sm font-medium ${isDarkMode ? 'text-gray-300' : 'text-gray-700'}`}>Saved Filters</h3>
            <button
              type="button"
              onClick={() => setShowSaveFilter(!showSaveFilter)}
              className={`text-xs ${isDarkMode ? 'text-blue-400' : 'text-blue-600'}`}
            >
              {showSaveFilter ? 'Cancel' : 'Save Current Filter'}
            </button>
          </div>
          
          {/* Save filter form */}
          {showSaveFilter && (
            <div className="mt-2 flex space-x-2">
              <input
                type="text"
                placeholder="Filter name"
                value={saveFilterName}
                onChange={(e) => setSaveFilterName(e.target.value)}
                className={`flex-1 px-3 py-1 border rounded-md shadow-sm text-sm focus:ring-blue-500 focus:border-blue-500 ${
                  isDarkMode ? 'bg-gray-700 border-gray-600 text-white placeholder-gray-400' : 'bg-white border-gray-300 text-gray-900 placeholder-gray-500'
                }`}
              />
              <button
                type="button"
                onClick={handleSaveFilter}
                disabled={!saveFilterName.trim()}
                className={`px-3 py-1 rounded-md shadow-sm text-sm font-medium text-white ${
                  saveFilterName.trim() ? 'bg-blue-600 hover:bg-blue-700' : 'bg-blue-400 cursor-not-allowed'
                }`}
              >
                Save
              </button>
            </div>
          )}
          
          {/* List of saved filters */}
          <div className="mt-2 space-y-1 max-h-32 overflow-y-auto">
            {savedFilters.map((filter) => (
              <button
                key={filter.name}
                type="button"
                onClick={() => handleLoadFilter(filter.name)}
                className={`flex items-center w-full px-2 py-1 text-left rounded-md text-sm ${
                  isDarkMode
                    ? 'hover:bg-gray-700 text-gray-300'
                    : 'hover:bg-gray-100 text-gray-800'
                }`}
              >
                <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 mr-1 text-blue-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 4a1 1 0 011-1h16a1 1 0 011 1v2.586a1 1 0 01-.293.707l-6.414 6.414a1 1 0 00-.293.707V17l-4 4v-6.586a1 1 0 00-.293-.707L3.293 7.293A1 1 0 013 6.586V4z" />
                </svg>
                {filter.name}
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default PropertyFilter;