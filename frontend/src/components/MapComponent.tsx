import React, { useEffect, useState, FC, useCallback, useMemo, useRef } from 'react';
import { MapContainer, TileLayer, Marker, Popup, useMap, ZoomControl } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import { Property } from '../types/property';
import { geocodeProperties, enhancedGeocodeProperties } from '../utils/geocoding';
import CustomMarkerClusterGroup from './map/CustomMarkerCluster';
// MarkerCluster CSS is loaded in _app.js/tsx instead of here to avoid Next.js CSS import restrictions
// Original import: import 'react-leaflet-cluster/lib/assets/MarkerCluster.Default.css';

// Map Legend component to show what the different marker colors mean
const MapLegend: FC = () => {
  const [expanded, setExpanded] = useState(false);
  
  return (
    <div className="absolute bottom-4 left-4 z-10 bg-white dark:bg-gray-800 rounded-lg shadow-md overflow-hidden">
      <div 
        className="px-3 py-2 font-semibold text-sm flex items-center justify-between cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-700"
        onClick={() => setExpanded(!expanded)}
      >
        <div className="flex items-center">
          <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-2 text-gray-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 20l-5.447-2.724A1 1 0 013 16.382V5.618a1 1 0 011.447-.894L9 7m0 13l6-3m-6 3V7m6 10l4.553 2.276A1 1 0 0021 18.382V7.618a1 1 0 00-.553-.894L15 4m0 13V4m0 0L9 7" />
          </svg>
          <span>Legend & Filters</span>
        </div>
        <svg xmlns="http://www.w3.org/2000/svg" className={`h-5 w-5 transform transition-transform ${expanded ? 'rotate-180' : ''}`} fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </div>
      
      {expanded && (
        <div className="px-3 py-2 border-t border-gray-200 dark:border-gray-700">
          {/* Price Range Filter */}
          <div className="mb-4">
            <div className="text-xs font-medium text-gray-500 dark:text-gray-400 mb-2 flex items-center justify-between">
              <span>Price Range</span>
              <button className="text-primary hover:text-primary/80 text-xs">Reset</button>
            </div>
            <div className="space-y-1">
              {[
                { color: 'purple-500', label: 'Premium ($20M+)', value: 'premium' },
                { color: 'blue-800', label: 'High ($10M-$20M)', value: 'high' },
                { color: 'blue-500', label: 'Mid-High ($5M-$10M)', value: 'mid-high' },
                { color: 'green-500', label: 'Medium ($1M-$5M)', value: 'medium' },
                { color: 'yellow-500', label: 'Affordable (Under $1M)', value: 'affordable' }
              ].map(range => (
                <label key={range.value} className="flex items-center text-xs cursor-pointer">
                  <input
                    type="checkbox"
                    className="form-checkbox h-3 w-3 text-primary rounded border-gray-300"
                    value={range.value}
                  />
                  <div className={`w-3 h-3 rounded-full bg-${range.color} mx-2`}></div>
                  <span>{range.label}</span>
                </label>
              ))}
            </div>
          </div>

          {/* Status Filter */}
          <div className="mb-4">
            <div className="text-xs font-medium text-gray-500 dark:text-gray-400 mb-2 flex items-center justify-between">
              <span>Status</span>
              <button className="text-primary hover:text-primary/80 text-xs">Reset</button>
            </div>
            <div className="space-y-1">
              {[
                { color: 'green-500', label: 'Available', value: 'available' },
                { color: 'yellow-500', label: 'Under Contract', value: 'under_contract' },
                { color: 'red-500', label: 'Sold', value: 'sold' }
              ].map(status => (
                <label key={status.value} className="flex items-center text-xs cursor-pointer">
                  <input
                    type="checkbox"
                    className="form-checkbox h-3 w-3 text-primary rounded border-gray-300"
                    value={status.value}
                  />
                  <div className={`w-3 h-3 rounded-full bg-${status.color} mx-2`}></div>
                  <span>{status.label}</span>
                </label>
              ))}
            </div>
          </div>

          {/* Additional Filters */}
          <div>
            <div className="text-xs font-medium text-gray-500 dark:text-gray-400 mb-2">
              Additional Filters
            </div>
            <div className="space-y-1">
              <label className="flex items-center text-xs cursor-pointer">
                <input
                  type="checkbox"
                  className="form-checkbox h-3 w-3 text-primary rounded border-gray-300"
                  value="has_price"
                />
                <span className="ml-2">Has Price Listed</span>
              </label>
              <label className="flex items-center text-xs cursor-pointer">
                <input
                  type="checkbox"
                  className="form-checkbox h-3 w-3 text-primary rounded border-gray-300"
                  value="has_units"
                />
                <span className="ml-2">Has Unit Count</span>
              </label>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

// Component to handle map initialization effects
const MapInitializer: FC = () => {
  useEffect(() => {
    // Fix Leaflet marker icon issue in Next.js
    try {
      // @ts-ignore
      delete L.Icon.Default.prototype._getIconUrl;
      L.Icon.Default.mergeOptions({
        iconUrl: '/icons/marker-blue.png',
        iconRetinaUrl: '/icons/marker-blue.png',
        shadowUrl: '/icons/marker-shadow.png',
      });
    } catch (e) {
      console.error('Error fixing Leaflet icon issue:', e);
    }
  }, []);
  
  return null;
};

// Custom marker icons for different property statuses
const createStatusIcon = (color: string) => new L.Icon({
  iconUrl: `https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-${color}.png`,
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/0.7.7/images/marker-shadow.png',
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
  shadowSize: [41, 41]
});

// Status icon mapping
const statusIcons = {
  'available': createStatusIcon('green'),
  'pending': createStatusIcon('yellow'),
  'under_contract': createStatusIcon('orange'),
  'sold': createStatusIcon('red'),
  'Actively Marketed': createStatusIcon('green'),
  'Under Contract': createStatusIcon('orange'),
  'Sold': createStatusIcon('red'),
  'default': new L.Icon.Default(),
};

interface MapRecenterProps {
  selectedProperty: Property | null;
}

// Component to recenter map when selectedProperty changes
const MapRecenter: FC<MapRecenterProps> = ({ selectedProperty }) => {
  const map = useMap();
  
  useEffect(() => {
    if (selectedProperty && 
        selectedProperty.latitude && 
        selectedProperty.longitude) {
          
      // Check if coordinates are valid (either from research or regular valid coordinates)
      const hasCoordinates = typeof selectedProperty.latitude === 'number' && 
                            typeof selectedProperty.longitude === 'number';
      const isNotZero = !(selectedProperty.latitude === 0 && selectedProperty.longitude === 0);
      const fromResearch = selectedProperty._coordinates_from_research === true;
      const isValid = fromResearch || 
                     (hasCoordinates && isNotZero && 
                      !selectedProperty._coordinates_missing && 
                      !selectedProperty._is_grid_pattern);
      
      if (isValid) {
        map.setView(
          [selectedProperty.latitude, selectedProperty.longitude],
          15,
          { animate: true }
        );
      }
    }
  }, [selectedProperty, map]);
  
  return null;
};

interface MapBoundsUpdaterProps {
  onBoundsChange: (bounds: any) => void;
}

// Component to track map bounds for filtering
const MapBoundsUpdater: FC<MapBoundsUpdaterProps> = ({ onBoundsChange }) => {
  const map = useMap();
  const [lastBounds, setLastBounds] = useState<any>(null);
  
  // Check if bounds have changed significantly to avoid too many reloads
  const hasBoundsChangedSignificantly = (newBounds: any, oldBounds: any) => {
    if (!oldBounds) return true;
    
    // Calculate area change ratio
    const oldArea = (oldBounds.north - oldBounds.south) * (oldBounds.east - oldBounds.west);
    const newArea = (newBounds.north - newBounds.south) * (newBounds.east - newBounds.west);
    
    // Calculate center shift distance
    const oldCenterLat = (oldBounds.north + oldBounds.south) / 2;
    const oldCenterLng = (oldBounds.east + oldBounds.west) / 2;
    const newCenterLat = (newBounds.north + newBounds.south) / 2;
    const newCenterLng = (newBounds.east + newBounds.west) / 2;
    
    const centerShift = Math.sqrt(
      Math.pow(newCenterLat - oldCenterLat, 2) + 
      Math.pow(newCenterLng - oldCenterLng, 2)
    );
    
    // Determine if bounds have changed enough to trigger a reload
    // Either the area has changed by 50% or more, or the center has shifted significantly
    const areaRatio = Math.max(newArea / oldArea, oldArea / newArea);
    return areaRatio > 1.5 || centerShift > 0.1;
  };
  
  const updateBoundsRef = useCallback(() => {
    const bounds = map.getBounds();
    const newBounds = {
      north: bounds.getNorth(),
      south: bounds.getSouth(),
      east: bounds.getEast(),
      west: bounds.getWest(),
    };
    
    // Check if bounds have changed significantly
    if (hasBoundsChangedSignificantly(newBounds, lastBounds)) {
      console.log('Map bounds changed significantly, triggering update');
      setLastBounds(newBounds);
      onBoundsChange(newBounds);
    }
  }, [map, onBoundsChange, lastBounds]);
  
  useEffect(() => {
    // Only run the initial update after a slight delay to ensure the map is fully loaded
    const initialTimeout = setTimeout(() => {
      updateBoundsRef();
    }, 500);
    
    // Add event listeners
    map.on('moveend', updateBoundsRef);
    map.on('zoomend', updateBoundsRef);
    
    // Cleanup listeners and timeout
    return () => {
      clearTimeout(initialTimeout);
      map.off('moveend', updateBoundsRef);
      map.off('zoomend', updateBoundsRef);
    };
  }, [map, updateBoundsRef]);
  
  return null;
};

interface MapFilterProps {
  onFilterChange: (filters: { showPremium: boolean; showAvailable: boolean; showUnderContract: boolean; showSold: boolean }) => void
}

// Add a simple filter component for the map
const MapFilter: FC<MapFilterProps> = ({ onFilterChange }) => {
  const [expanded, setExpanded] = useState(false);
  const [filters, setFilters] = useState({
    showPremium: true,
    showAvailable: true,
    showUnderContract: true,
    showSold: true
  });
  
  const handleFilterChange = (key: string, value: boolean) => {
    const newFilters = { ...filters, [key]: value };
    setFilters(newFilters);
    onFilterChange(newFilters);
  };
  
  return (
    <div className="absolute top-20 right-4 z-10 bg-white dark:bg-gray-800 rounded-lg shadow-md overflow-hidden">
      <div 
        className="px-3 py-2 font-semibold text-sm flex items-center justify-between cursor-pointer"
        onClick={() => setExpanded(!expanded)}
      >
        <div className="flex items-center">
          <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-2 text-gray-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 4a1 1 0 011-1h16a1 1 0 011 1v2.586a1 1 0 01-.293.707l-6.414 6.414a1 1 0 00-.293.707V17l-4 4v-6.586a1 1 0 00-.293-.707L3.293 7.293A1 1 0 013 6.586V4z" />
          </svg>
          Quick Filter
        </div>
        <svg xmlns="http://www.w3.org/2000/svg" className={`h-5 w-5 transform transition-transform ${expanded ? 'rotate-180' : ''}`} fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </div>
      
      {expanded && (
        <div className="px-3 py-2 border-t border-gray-200 dark:border-gray-700">
          <div className="grid grid-cols-1 gap-1">
            <label className="flex items-center text-sm">
              <input 
                type="checkbox" 
                className="form-checkbox h-4 w-4 mr-2 text-blue-600" 
                checked={filters.showPremium}
                onChange={(e) => handleFilterChange('showPremium', e.target.checked)}
              />
              Premium Properties
            </label>
            <label className="flex items-center text-sm">
              <input 
                type="checkbox" 
                className="form-checkbox h-4 w-4 mr-2 text-green-600" 
                checked={filters.showAvailable}
                onChange={(e) => handleFilterChange('showAvailable', e.target.checked)}
              />
              Available Properties
            </label>
            <label className="flex items-center text-sm">
              <input 
                type="checkbox" 
                className="form-checkbox h-4 w-4 mr-2 text-yellow-600" 
                checked={filters.showUnderContract}
                onChange={(e) => handleFilterChange('showUnderContract', e.target.checked)}
              />
              Under Contract
            </label>
            <label className="flex items-center text-sm">
              <input 
                type="checkbox" 
                className="form-checkbox h-4 w-4 mr-2 text-red-600" 
                checked={filters.showSold}
                onChange={(e) => handleFilterChange('showSold', e.target.checked)}
              />
              Sold Properties
            </label>
          </div>
        </div>
      )}
    </div>
  );
};

// Add a search component
const MapSearch: FC<{
  properties: Property[];
  onPropertySelect: (property: Property) => void;
}> = ({ properties, onPropertySelect }) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [showResults, setShowResults] = useState(false);
  const searchRef = useRef<HTMLDivElement>(null);

  // Close search results when clicking outside
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (searchRef.current && !searchRef.current.contains(event.target as Node)) {
        setShowResults(false);
      }
    }

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleSearchChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const term = e.target.value;
    setSearchTerm(term);
    
    if (term.length < 2) {
      setFilteredResults([]);
      return;
    }

    const searchLower = term.toLowerCase();
    const results = properties
      .filter(property => {
        const matchName = property.name?.toLowerCase().includes(searchLower);
        const matchAddress = property.address?.toLowerCase().includes(searchLower);
        const matchBroker = property.broker?.name?.toLowerCase().includes(searchLower);
        return matchName || matchAddress || matchBroker;
      })
      .slice(0, 5); // Limit to 5 results for better performance

    setFilteredResults(results);
    setShowResults(true);
  };

  const handleSelect = (property: Property) => {
    onPropertySelect(property);
    setSearchTerm('');
    setShowResults(false);
  };

  const formatPrice = (price: number | undefined) => {
    if (!price) return 'Price on request';
    return price >= 1000000 
      ? `$${(price / 1000000).toFixed(1)}M` 
      : `$${(price / 1000).toFixed(0)}K`;
  };

  return (
    <div ref={searchRef} className="absolute top-4 left-4 z-10 w-80">
      <div className="relative">
        <input
          type="text"
          value={searchTerm}
          onChange={handleSearchChange}
          placeholder="Search properties by name, address, or broker..."
          className="w-full px-4 py-2 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-700 rounded-lg shadow-sm focus:ring-2 focus:ring-primary focus:border-transparent"
        />
        {searchTerm && (
          <button
            onClick={() => {
              setSearchTerm('');
              setShowResults(false);
            }}
            className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
          >
            <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
            </svg>
          </button>
        )}
      </div>
      
      {showResults && filteredResults.length > 0 && (
        <div className="absolute w-full mt-1 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg shadow-lg overflow-hidden">
          {filteredResults.map((property) => (
            <button
              key={property.id}
              onClick={() => handleSelect(property)}
              className="w-full px-4 py-3 text-left hover:bg-gray-50 dark:hover:bg-gray-700 border-b last:border-b-0 border-gray-200 dark:border-gray-700 flex items-start gap-3"
            >
              <div className="flex-shrink-0 w-12 h-12 bg-gray-100 dark:bg-gray-600 rounded overflow-hidden">
                {property.image_url ? (
                  <img 
                    src={property.image_url} 
                    alt={property.name} 
                    className="w-full h-full object-cover"
                  />
                ) : (
                  <div className="w-full h-full flex items-center justify-center">
                    <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
                    </svg>
                  </div>
                )}
              </div>
              <div className="flex-1 min-w-0">
                <div className="font-medium text-sm truncate">{property.name}</div>
                <div className="text-xs text-gray-500 dark:text-gray-400 truncate">{property.address}</div>
                <div className="mt-1 flex items-center gap-2">
                  <span className="text-xs font-medium">{formatPrice(property.price)}</span>
                  {property.units && (
                    <span className="text-xs text-gray-500 dark:text-gray-400">{property.units} units</span>
                  )}
                </div>
              </div>
            </button>
          ))}
        </div>
      )}
      
      {showResults && searchTerm && filteredResults.length === 0 && (
        <div className="absolute w-full mt-1 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg shadow-lg">
          <div className="px-4 py-3 text-sm text-gray-500 dark:text-gray-400 text-center">
            No properties found matching "{searchTerm}"
          </div>
        </div>
      )}
    </div>
  );
};

// Add new PropertiesList component
const PropertiesList: FC<{
  properties: Property[];
  onPropertySelect: (property: Property) => void;
  mapFilters: {
    showPremium: boolean;
    showAvailable: boolean;
    showUnderContract: boolean;
    showSold: boolean;
  };
  setMapFilters: (filters: any) => void;
}> = ({ properties, onPropertySelect, mapFilters, setMapFilters }) => {
  const [sortBy, setSortBy] = useState<string>('recent');
  const [unitFilter, setUnitFilter] = useState<[number, number]>([0, 1000]);
  const [yearFilter, setYearFilter] = useState<[number, number]>([1900, new Date().getFullYear()]);
  const [searchTerm, setSearchTerm] = useState('');

  // Calculate ranges for filters
  const ranges = useMemo(() => {
    const units = properties.map(p => p.num_units || p.units || 0);
    const years = properties.map(p => p.year_built || 0).filter(y => y > 0);
    return {
      units: {
        min: Math.min(...units),
        max: Math.max(...units)
      },
      years: {
        min: Math.min(...years),
        max: Math.max(...years)
      }
    };
  }, [properties]);

  // Filter and sort properties
  const filteredAndSortedProperties = useMemo(() => {
    return properties
      .filter(property => {
        // Status filters
        const status = (property.status || '').toLowerCase();
        if (status.includes('contract') || status.includes('pending')) {
          if (!mapFilters.showUnderContract) return false;
        } else if (status.includes('sold')) {
          if (!mapFilters.showSold) return false;
        } else {
          if (!mapFilters.showAvailable) return false;
        }

        // Premium filter
        if (property.price && property.price >= 10000000) {
          if (!mapFilters.showPremium) return false;
        }

        // Unit filter
        const units = property.num_units || property.units || 0;
        if (units < unitFilter[0] || units > unitFilter[1]) return false;

        // Year filter
        const year = property.year_built || 0;
        if (year && (year < yearFilter[0] || year > yearFilter[1])) return false;

        // Search term
        if (searchTerm) {
          const searchLower = searchTerm.toLowerCase();
          return (
            property.name?.toLowerCase().includes(searchLower) ||
            property.address?.toLowerCase().includes(searchLower) ||
            property.broker?.name?.toLowerCase().includes(searchLower)
          );
        }

        return true;
      })
      .sort((a, b) => {
        switch (sortBy) {
          case 'units-high':
            return (b.num_units || b.units || 0) - (a.num_units || a.units || 0);
          case 'units-low':
            return (a.num_units || a.units || 0) - (b.num_units || b.units || 0);
          case 'year-new':
            return (b.year_built || 0) - (a.year_built || 0);
          case 'year-old':
            return (a.year_built || 0) - (b.year_built || 0);
          case 'recent':
          default:
            return new Date(b.created_at || 0).getTime() - new Date(a.created_at || 0).getTime();
        }
      });
  }, [properties, mapFilters, unitFilter, yearFilter, searchTerm, sortBy]);

  return (
    <div className="absolute left-0 top-0 h-full w-96 bg-white dark:bg-gray-800 shadow-lg flex flex-col">
      {/* Header */}
      <div className="p-4 border-b border-gray-200 dark:border-gray-700">
        <h2 className="text-lg font-semibold mb-2">Properties</h2>
        <div className="relative">
          <input
            type="text"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder="Search properties..."
            className="w-full px-3 py-2 bg-gray-50 dark:bg-gray-700 rounded-lg text-sm"
          />
          {searchTerm && (
            <button
              onClick={() => setSearchTerm('')}
              className="absolute right-2 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
            >
              <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" viewBox="0 0 20 20" fill="currentColor">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
              </svg>
            </button>
          )}
        </div>
      </div>

      {/* Filters */}
      <div className="p-4 border-b border-gray-200 dark:border-gray-700 space-y-4">
        {/* Sort dropdown */}
        <div>
          <label className="block text-sm font-medium mb-1">Sort By</label>
          <select
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value)}
            className="w-full px-3 py-2 bg-gray-50 dark:bg-gray-700 rounded-lg text-sm"
          >
            <option value="recent">Most Recent</option>
            <option value="units-high">Units (High to Low)</option>
            <option value="units-low">Units (Low to High)</option>
            <option value="year-new">Year Built (Newest)</option>
            <option value="year-old">Year Built (Oldest)</option>
          </select>
        </div>

        {/* Status filters */}
        <div>
          <label className="block text-sm font-medium mb-2">Status</label>
          <div className="space-y-2">
            <label className="flex items-center">
              <input
                type="checkbox"
                checked={mapFilters.showAvailable}
                onChange={(e) => setMapFilters({ ...mapFilters, showAvailable: e.target.checked })}
                className="form-checkbox h-4 w-4 text-blue-600"
              />
              <span className="ml-2 text-sm">Available</span>
            </label>
            <label className="flex items-center">
              <input
                type="checkbox"
                checked={mapFilters.showUnderContract}
                onChange={(e) => setMapFilters({ ...mapFilters, showUnderContract: e.target.checked })}
                className="form-checkbox h-4 w-4 text-yellow-600"
              />
              <span className="ml-2 text-sm">Under Contract</span>
            </label>
            <label className="flex items-center">
              <input
                type="checkbox"
                checked={mapFilters.showSold}
                onChange={(e) => setMapFilters({ ...mapFilters, showSold: e.target.checked })}
                className="form-checkbox h-4 w-4 text-red-600"
              />
              <span className="ml-2 text-sm">Sold</span>
            </label>
          </div>
        </div>

        {/* Unit range filter */}
        <div>
          <label className="block text-sm font-medium mb-2">
            Units Range: {unitFilter[0]} - {unitFilter[1]}
          </label>
          <div className="px-2">
            <input
              type="range"
              min={ranges.units.min}
              max={ranges.units.max}
              value={unitFilter[0]}
              onChange={(e) => setUnitFilter([parseInt(e.target.value), unitFilter[1]])}
              className="w-full"
            />
            <input
              type="range"
              min={ranges.units.min}
              max={ranges.units.max}
              value={unitFilter[1]}
              onChange={(e) => setUnitFilter([unitFilter[0], parseInt(e.target.value)])}
              className="w-full"
            />
          </div>
        </div>

        {/* Year built filter */}
        <div>
          <label className="block text-sm font-medium mb-2">
            Year Built: {yearFilter[0]} - {yearFilter[1]}
          </label>
          <div className="px-2">
            <input
              type="range"
              min={ranges.years.min}
              max={ranges.years.max}
              value={yearFilter[0]}
              onChange={(e) => setYearFilter([parseInt(e.target.value), yearFilter[1]])}
              className="w-full"
            />
            <input
              type="range"
              min={ranges.years.min}
              max={ranges.years.max}
              value={yearFilter[1]}
              onChange={(e) => setYearFilter([yearFilter[0], parseInt(e.target.value)])}
              className="w-full"
            />
          </div>
        </div>
      </div>

      {/* Properties list */}
      <div className="flex-1 overflow-y-auto">
        {filteredAndSortedProperties.length === 0 ? (
          <div className="p-4 text-center text-gray-500">
            No properties match your filters
          </div>
        ) : (
          <div className="divide-y divide-gray-200 dark:divide-gray-700">
            {filteredAndSortedProperties.map((property) => (
              <div
                key={property.id}
                onClick={() => onPropertySelect(property)}
                className="p-4 hover:bg-gray-50 dark:hover:bg-gray-700 cursor-pointer"
              >
                <div className="flex items-start gap-3">
                  <div className="flex-shrink-0 w-16 h-16 bg-gray-100 dark:bg-gray-600 rounded overflow-hidden">
                    {property.image_url ? (
                      <img
                        src={property.image_url}
                        alt={property.name}
                        className="w-full h-full object-cover"
                      />
                    ) : (
                      <div className="w-full h-full flex items-center justify-center">
                        <svg xmlns="http://www.w3.org/2000/svg" className="h-8 w-8 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
                        </svg>
                      </div>
                    )}
                  </div>
                  <div className="flex-1 min-w-0">
                    <h3 className="text-sm font-medium truncate">{property.name}</h3>
                    <p className="text-xs text-gray-500 dark:text-gray-400 mt-1 truncate">
                      {property.address}
                    </p>
                    <div className="mt-2 flex items-center gap-2">
                      <span className={`px-2 py-0.5 rounded-full text-xs ${
                        property.status?.toLowerCase().includes('available') || 
                        property.status?.toLowerCase().includes('active')
                          ? 'bg-green-100 text-green-800' 
                          : property.status?.toLowerCase().includes('contract')
                          ? 'bg-yellow-100 text-yellow-800' 
                          : 'bg-red-100 text-red-800'
                      }`}>
                        {property.status?.toLowerCase().includes('available') || 
                         property.status?.toLowerCase().includes('active')
                          ? 'Available'
                          : property.status?.toLowerCase().includes('contract')
                          ? 'Under Contract'
                          : property.status || 'Unknown'}
                      </span>
                      {(property.num_units || property.units) && (
                        <span className="text-xs text-gray-500">
                          {property.num_units || property.units} units
                        </span>
                      )}
                      {property.year_built && (
                        <span className="text-xs text-gray-500">
                          Built {property.year_built}
                        </span>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

interface MapComponentProps {
  properties: Property[];
  selectedProperty: Property | null;
  setSelectedProperty: (property: Property | null) => void;
  onBoundsChange?: (bounds: any) => void;
  mapboxToken?: string;
}

const MapComponent: FC<MapComponentProps> = ({ 
  properties, 
  selectedProperty, 
  setSelectedProperty,
  onBoundsChange,
  mapboxToken 
}) => {
  // State for geocoded properties
  const [processedProperties, setProcessedProperties] = useState<Property[]>(properties || []);
  const [geocodingStatus, setGeocodingStatus] = useState({
    isGeocoding: false,
    count: 0,
    total: 0
  });
  
  // Filter state
  const [mapFilters, setMapFilters] = useState({
    showPremium: true,
    showAvailable: true,
    showUnderContract: true,
    showSold: true
  });
  
  // Get Mapbox token from environment, with fallback to ensure map loads
  const mapboxTokenEnv = process.env.NEXT_PUBLIC_MAPBOX_TOKEN || '';
  const [mapLoaded, setMapLoaded] = useState(false);
  const [mapError, setMapError] = useState<string | null>(null);
  
  // Properly verify token format to avoid map loading issues
  const isValidMapboxToken = useMemo(() => {
    return mapboxTokenEnv && mapboxTokenEnv.startsWith('pk.') && mapboxTokenEnv.length > 20;
  }, [mapboxTokenEnv]);

  // For Austin, TX
  const defaultCenter: [number, number] = [30.2672, -97.7431];
  const defaultZoom = 12;
  
  // Debug variables
  useEffect(() => {
    if (!properties || !Array.isArray(properties)) {
      console.log('No properties available');
      return;
    }
    
    console.log(`===== MAP COMPONENT DEBUG =====`);
    console.log(`Received ${properties.length} properties from parent`);
    
    // Analyze properties before filtering
    const withLat = properties.filter(p => p.latitude).length;
    const withLng = properties.filter(p => p.longitude).length;
    const withBoth = properties.filter(p => p.latitude && p.longitude).length;
    const validNumbers = properties.filter(p => 
      typeof p.latitude === 'number' && 
      typeof p.longitude === 'number'
    ).length;
    const nonZero = properties.filter(p => 
      p.latitude !== 0 && 
      p.longitude !== 0
    ).length;
    
    console.log(`Properties with lat: ${withLat}, with lng: ${withLng}, with both: ${withBoth}`);
    console.log(`Properties with numeric coordinates: ${validNumbers}`);
    console.log(`Properties with non-zero coordinates: ${nonZero}`);
    
    // Check validity using our internal function
    const passesValidation = properties.filter(p => hasValidCoordinates(p)).length;
    console.log(`Properties that pass hasValidCoordinates(): ${passesValidation}`);
    
    // Check final filtered result
    setTimeout(() => {
      console.log(`RESULT: Displaying ${propertiesWithCoordinates.length} properties on map`);
      console.log(`===== END MAP COMPONENT DEBUG =====`);
    }, 100); // Small delay to ensure propertiesWithCoordinates has been calculated
  }, [properties]);

  // Fix for properties geocoding with Promise.then
  useEffect(() => {
    if (geocodingStatus.isGeocoding && properties) {
      // Find properties needing geocoding (filter out those with valid coordinates)
      const batchToGeocode = properties.filter(property => {
        return (
          (!property.latitude || !property.longitude || 
           property.latitude === 0 || property.longitude === 0 ||
           property._is_grid_pattern || property._needs_geocoding) && 
          !property._geocoding_failed
        );
      });
      
      console.log(`MapComponent: Geocoding batch of ${batchToGeocode.length} properties`);
      
      // Use enhanced geocoding with multiple methods (fixed Promise handling)
      if (batchToGeocode.length > 0) {
        try {
          // Call the geocoding function, but don't rely on its direct return type
          const geocodeResult = enhancedGeocodeProperties(batchToGeocode);
          
          // Use a safer approach - create a Promise that will handle the result appropriately
          Promise.resolve(geocodeResult)
            .then(geocodedProperties => {
              // Safety check that we got an array of properties back
              if (!Array.isArray(geocodedProperties)) {
                throw new Error('Geocoding did not return an array of properties');
              }
              
              // Count how many were successfully geocoded
              const newlyGeocodedCount = geocodedProperties.filter(p => p._geocoded).length;
              
              console.log(`MapComponent: Successfully geocoded ${newlyGeocodedCount} properties`);
              
              // Merge geocoded properties with existing properties
              const updatedProperties = [...properties];
              geocodedProperties.forEach(geocodedProperty => {
                const index = updatedProperties.findIndex(p => p.id === geocodedProperty.id);
                if (index !== -1) {
                  updatedProperties[index] = geocodedProperty;
                }
              });
              
              setProcessedProperties(updatedProperties);
              setGeocodingStatus({
                isGeocoding: false,
                count: newlyGeocodedCount,
                total: batchToGeocode.length
              });
            })
            .catch(error => {
              console.error('Error geocoding properties:', error);
              setGeocodingStatus({
                isGeocoding: false,
                count: 0,
                total: batchToGeocode.length
              });
            });
        } catch (error) {
          console.error('Error initiating geocoding:', error);
          setGeocodingStatus({
            isGeocoding: false,
            count: 0,
            total: batchToGeocode.length
          });
        }
      } else {
        // No properties to geocode
        setGeocodingStatus({
          isGeocoding: false,
          count: 0,
          total: 0
        });
      }
    }
  }, [properties, geocodingStatus.isGeocoding]);
  
  // Setup default marker icons
  L.Marker.prototype.options.icon = L.icon({
    iconUrl: '/icons/marker-blue.png',
    iconSize: [25, 41],
    iconAnchor: [12, 41],
    popupAnchor: [1, -34],
    shadowSize: [41, 41]
  });

  // Add helper function to get the right marker icon based on property status and price
  const getMarkerIcon = (property: Property) => {
    // If the property has verified coordinates, use a verified icon
    if (property.verified_address) {
      return L.icon({
        iconUrl: '/icons/marker-verified.png',
        iconSize: [25, 41],
        iconAnchor: [12, 41],
        popupAnchor: [1, -34],
        shadowSize: [41, 41]
      });
    }
    
    // If the property has coordinate issues, use a warning icon
    if (property._is_grid_pattern || property._is_invalid_range || 
        property._outside_austin || property._coordinates_from_research) {
      return L.icon({
        iconUrl: '/icons/marker-warning.png',
        iconSize: [25, 41],
        iconAnchor: [12, 41],
        popupAnchor: [1, -34],
        shadowSize: [41, 41]
      });
    }
    
    // For test properties
    if (property._is_test_property) {
      return L.icon({
        iconUrl: '/icons/marker-test.png',
        iconSize: [25, 41],
        iconAnchor: [12, 41],
        popupAnchor: [1, -34],
        shadowSize: [41, 41]
      });
    }
    
    // For geocoded properties
    if (property._geocoded) {
      return L.icon({
        iconUrl: '/icons/marker-geocoded.png',
        iconSize: [25, 41],
        iconAnchor: [12, 41],
        popupAnchor: [1, -34],
        shadowSize: [41, 41]
      });
    }
    
    // Color code by price range if price is available
    if (property.price) {
      const price = property.price;
      
      // Premium properties (>$20M)
      if (price >= 20000000) {
        return L.icon({
          iconUrl: '/icons/marker-purple.png',
          iconSize: [25, 41],
          iconAnchor: [12, 41],
          popupAnchor: [1, -34],
          shadowSize: [41, 41]
        });
      }
      
      // High-value properties ($10M-$20M)
      if (price >= 10000000) {
        return L.icon({
          iconUrl: '/icons/marker-dark-blue.png',
          iconSize: [25, 41],
          iconAnchor: [12, 41],
          popupAnchor: [1, -34],
          shadowSize: [41, 41]
        });
      }
      
      // Mid-high properties ($5M-$10M)
      if (price >= 5000000) {
        return L.icon({
          iconUrl: '/icons/marker-blue.png',
          iconSize: [25, 41],
          iconAnchor: [12, 41],
          popupAnchor: [1, -34],
          shadowSize: [41, 41]
        });
      }
      
      // Medium properties ($1M-$5M)
      if (price >= 1000000) {
        return L.icon({
          iconUrl: '/icons/marker-green.png',
          iconSize: [25, 41],
          iconAnchor: [12, 41],
          popupAnchor: [1, -34],
          shadowSize: [41, 41]
        });
      }
      
      // Affordable properties (<$1M)
      return L.icon({
        iconUrl: '/icons/marker-yellow.png',
        iconSize: [25, 41],
        iconAnchor: [12, 41],
        popupAnchor: [1, -34],
        shadowSize: [41, 41]
      });
    }
    
    // Default marker icons based on status if no price
    const status = property.status?.toLowerCase() || '';
    if (status === 'active' || status === 'listed' || status === 'available' || status === 'actively marketed') {
      return L.icon({
        iconUrl: '/icons/marker-green.png',
        iconSize: [25, 41],
        iconAnchor: [12, 41],
        popupAnchor: [1, -34],
        shadowSize: [41, 41]
      });
    } else if (status.includes('contract') || status.includes('pending')) {
      return L.icon({
        iconUrl: '/icons/marker-yellow.png',
        iconSize: [25, 41],
        iconAnchor: [12, 41],
        popupAnchor: [1, -34],
        shadowSize: [41, 41]
      });
    } else if (status.includes('sold')) {
      return L.icon({
        iconUrl: '/icons/marker-red.png',
        iconSize: [25, 41],
        iconAnchor: [12, 41],
        popupAnchor: [1, -34],
        shadowSize: [41, 41]
      });
    }
    
    // Default fallback
    return L.icon({
      iconUrl: '/icons/marker-blue.png',
      iconSize: [25, 41],
      iconAnchor: [12, 41],
      popupAnchor: [1, -34],
      shadowSize: [41, 41]
    });
  };

  // Format price as $X.XM
  const formatPrice = (price: number | undefined) => {
    if (!price) return 'Price not available';
    if (price >= 1000000) {
      return `$${(price / 1000000).toFixed(1)}M`;
    }
    return `$${(price / 1000).toFixed(0)}K`;
  };

  // Format price per unit
  const formatPricePerUnit = (price: number | undefined, units: number | undefined) => {
    if (!price || !units || units === 0) return 'N/A';
    return `$${Math.round(price / units).toLocaleString()}/unit`;
  };

  // Add code to check coordinates and filter out invalid ones
  const validProperties = useMemo(() => {
    if (!properties || !Array.isArray(properties)) {
      return [];
    }
    
    // MODIFIED: Use much less strict filtering to show more properties
    return properties.filter(property => {
      // We need latitude and longitude to be defined
      if (!property || property.latitude === undefined || property.longitude === undefined) {
        return false;
      }

      // Convert string coordinates to numbers if needed
      const lat = typeof property.latitude === 'number' ? property.latitude : parseFloat(String(property.latitude));
      const lng = typeof property.longitude === 'number' ? property.longitude : parseFloat(String(property.longitude));

      // Check if coordinates are valid numbers
      if (isNaN(lat) || isNaN(lng)) {
        return false;
      }

      // Only exclude coordinates that are exactly zero (as these are likely placeholder data)
      // This allows for coordinates near zero but not exactly zero
      if (lat === 0 && lng === 0) {
        return false;
      }

      // Check if coordinates are within reasonable global ranges
      if (lat < -90 || lat > 90 || lng < -180 || lng > 180) {
        return false;
      }

      // Include all valid properties regardless of whether they're in Austin
      // Include properties even if they have grid patterns or are from research
      return true;
    });
  }, [properties]);
  
  // Check if property has valid coordinates - MODIFIED to be much less strict
  const hasValidCoordinates = (property: Property): boolean => {
    if (!property) return false;
    
    // Basic existence checks
    if (property.latitude === undefined || property.longitude === undefined) return false;
    
    // Convert to numbers if needed
    const lat = typeof property.latitude === 'number' ? property.latitude : parseFloat(String(property.latitude));
    const lng = typeof property.longitude === 'number' ? property.longitude : parseFloat(String(property.longitude));
    
    // Check for NaN
    if (isNaN(lat) || isNaN(lng)) return false;
    
    // Check for zero values (often default)
    if (lat === 0 && lng === 0) return false;
    
    // Check for reasonable coordinate ranges
    if (lat < -90 || lat > 90 || lng < -180 || lng > 180) return false;
    
    // Don't filter out properties based on location or data source
    // Include properties with _is_grid_pattern and _coordinates_from_research
    return true;
  };
  
  // Get properties with valid coordinates - MODIFIED to directly use validProperties
  const propertiesWithCoordinates = validProperties;

  // Add filter logic for properties
  const filteredProperties = useMemo(() => {
    // Log the number of valid properties
    console.log(`Valid properties before filtering: ${validProperties.length} of ${properties?.length || 0}`);
    
    // Count properties by some key attributes
    const propertiesWithResearchCoords = validProperties.filter(p => p._coordinates_from_research).length;
    const propertiesWithGridPattern = validProperties.filter(p => p._is_grid_pattern).length;
    console.log(`Properties with research coordinates: ${propertiesWithResearchCoords}`);
    console.log(`Properties with grid pattern: ${propertiesWithGridPattern}`);
    
    // Apply less strict filtering to show more properties on the map
    return validProperties.filter(property => {
      // Filter by price for premium properties (over $10M)
      if (property.price && property.price >= 10000000) {
        if (!mapFilters.showPremium) return false;
      }
      
      // Filter by status
      const status = (property.status || '').toLowerCase();
      
      if (status.includes('contract') || status.includes('pending')) {
        return mapFilters.showUnderContract;
      } else if (status.includes('sold')) {
        return mapFilters.showSold;
      } else {
        // Available, listed, etc.
        return mapFilters.showAvailable;
      }
    });
  }, [validProperties, mapFilters, properties?.length]);
  
  // New function to check if there are multiple properties at the same location
  const findPropertiesAtSameLocation = (targetProperty: Property) => {
    if (!targetProperty || !targetProperty.latitude || !targetProperty.longitude) {
      return [];
    }
    
    const lat = targetProperty.latitude;
    const lng = targetProperty.longitude;
    
    // Find properties that have the exact same coordinates (using exact match)
    // This is important for properties that have exactly the same coordinates
    return filteredProperties.filter(p => 
      p.id !== targetProperty.id && 
      p.latitude === lat && 
      p.longitude === lng
    );
  };

  // Debug the number of properties at the same locations - useful for understanding clustering issues
  useEffect(() => {
    if (filteredProperties.length === 0) return;
    
    // Count how many properties are at the same coordinates as others
    let sameLocationCount = 0;
    const checkedIds = new Set<string | number>();
    
    filteredProperties.forEach(property => {
      if (checkedIds.has(property.id)) return;
      
      const sameLocationProps = findPropertiesAtSameLocation(property);
      if (sameLocationProps.length > 0) {
        sameLocationCount += sameLocationProps.length + 1; // Include the current property
        
        // Mark all these properties as checked
        checkedIds.add(property.id);
        sameLocationProps.forEach(p => checkedIds.add(p.id));
        
        // Log the first few instances of exact-coordinate properties for debugging
        if (checkedIds.size < 20) {
          console.log(`Found ${sameLocationProps.length + 1} properties at the same location: ${property.latitude}, ${property.longitude}`);
          console.log(`  First property: ${property.name || property.id}`);
          sameLocationProps.slice(0, 3).forEach(p => {
            console.log(`  Other property: ${p.name || p.id}`);
          });
          if (sameLocationProps.length > 3) {
            console.log(`  ...and ${sameLocationProps.length - 3} more`);
          }
        }
      }
    });
    
    console.log(`Total properties at the same locations: ${sameLocationCount} (${Math.round(sameLocationCount/filteredProperties.length*100)}% of all displayed properties)`);
    
  }, [filteredProperties]);

  // Handle map load success
  const handleMapLoad = useCallback(() => {
    setMapLoaded(true);
    setMapError(null);
  }, []);
  
  // Handle map load error
  const handleMapError = useCallback((e: any) => {
    console.error('Map tile loading error:', e);
    setMapError('Failed to load map tiles. Using fallback map provider.');
    // Continue with OpenStreetMap as fallback
  }, []);

  return (
    <div className="relative h-full w-full">
      {/* Properties List Panel */}
      <PropertiesList 
        properties={properties} 
        onPropertySelect={setSelectedProperty}
        mapFilters={mapFilters}
        setMapFilters={setMapFilters}
      />
      
      {/* Existing map container with adjusted margin for list panel */}
      <div className="ml-96 h-full">
        <MapContainer 
          center={defaultCenter} 
          zoom={defaultZoom}
          style={{ height: '100%', width: '100%' }}
          zoomControl={false}
          whenReady={handleMapLoad}
        >
          <MapInitializer />
          
          {/* Use Mapbox if token is provided and valid, otherwise use OpenStreetMap */}
          {isValidMapboxToken ? (
            <TileLayer
              attribution='© <a href="https://www.mapbox.com/about/maps/">Mapbox</a>'
              url={`https://api.mapbox.com/styles/v1/mapbox/streets-v11/tiles/{z}/{x}/{y}?access_token=${mapboxTokenEnv}`}
              tileSize={512}
              zoomOffset={-1}
              eventHandlers={{
                error: handleMapError
              }}
            />
          ) : (
            <TileLayer
              attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
              url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
            />
          )}
          
          {/* Show map error if there is one */}
          {mapError && (
            <div className="absolute top-4 left-1/2 transform -translate-x-1/2 bg-red-100 text-red-700 px-4 py-2 rounded-md shadow-md z-50">
              {mapError}
            </div>
          )}
          
          {/* Map markers for properties */}
          {filteredProperties.length > 0 && (
            <CustomMarkerClusterGroup
              // These props will be merged with the enhanced props in CustomMarkerClusterGroup
              chunkedLoading={true}
              showCoverageOnHover={false}  // Disable coverage display which can be distracting
              disableClusteringAtZoom={18} // Disable clustering at maximum zoom
            >
              {filteredProperties
                .filter(property => 
                  typeof property.latitude === 'number' && 
                  typeof property.longitude === 'number'
                )
                .map((property) => {
                  // Find properties at same location
                  const sameLocationProperties = findPropertiesAtSameLocation(property);
                  const hasMultipleProperties = sameLocationProperties.length > 0;
                  
                  return (
                  <Marker
                    key={property.id}
                    position={[property.latitude as number, property.longitude as number]}
                    icon={getMarkerIcon(property)}
                    eventHandlers={{
                      click: () => {
                        // Find the original property in the properties array to make sure we have the latest data
                        const originalProperty = properties.find(p => p.id === property.id) || property;
                        setSelectedProperty(originalProperty);
                      },
                    }}
                  >
                    <Popup>
                      <div className="min-w-[220px]">
                        <div className="flex items-start justify-between">
                          <h3 className="font-bold text-lg">{property.name}</h3>
                          {/* Normalize and display status */}
                          <span className={`px-2 py-1 rounded-full text-xs ${
                            property.status?.toLowerCase().includes('available') || 
                            property.status?.toLowerCase().includes('active') || 
                            property.status === 'Actively Marketed'
                              ? 'bg-green-100 text-green-800' 
                              : property.status?.toLowerCase().includes('contract') || 
                                property.status?.toLowerCase().includes('pending')
                              ? 'bg-yellow-100 text-yellow-800' 
                              : 'bg-red-100 text-red-800'
                          }`}>
                            {property.status?.toLowerCase().includes('available') || 
                             property.status?.toLowerCase().includes('active') 
                              ? 'Available'
                              : property.status?.toLowerCase().includes('contract')
                              ? 'Under Contract'
                              : property.status || 'Unknown'}
                          </span>
                        </div>
                        
                        {/* Address with verification */}
                        <div className="mt-2">
                          <p className="text-gray-600 flex items-center">
                            <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 mr-1 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
                            </svg>
                            {property.verified_address || property.address}
                            {property.verified_address && (
                              <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 ml-1 text-green-500" viewBox="0 0 20 20" fill="currentColor">
                                <path fillRule="evenodd" d="M6.267 3.455a3.066 3.066 0 001.745-.723 3.066 3.066 0 013.976 0 3.066 3.066 0 001.745.723 3.066 3.066 0 012.812 2.812c.051.643.304 1.254.723 1.745a3.066 3.066 0 010 3.976 3.066 3.066 0 00-.723 1.745 3.066 3.066 0 01-2.812 2.812 3.066 3.066 0 00-1.745.723 3.066 3.066 0 01-3.976 0 3.066 3.066 0 00-1.745-.723 3.066 3.066 0 01-2.812-2.812 3.066 3.066 0 00-.723-1.745 3.066 3.066 0 010-3.976 3.066 3.066 0 00.723-1.745 3.066 3.066 0 012.812-2.812zm7.44 5.252a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                              </svg>
                            )}
                          </p>
                        </div>

                        {/* Property details grid */}
                        <div className="grid grid-cols-2 gap-3 mt-3">
                          <div className="bg-gray-50 p-2 rounded">
                            <span className="text-gray-500 text-xs block">Units</span>
                            <p className="font-medium">{property.num_units || property.units || 'N/A'}</p>
                          </div>
                          <div className="bg-gray-50 p-2 rounded">
                            <span className="text-gray-500 text-xs block">Year Built</span>
                            <p className="font-medium">{property.year_built || 'N/A'}</p>
                          </div>
                          {property.square_feet && (
                            <div className="bg-gray-50 p-2 rounded">
                              <span className="text-gray-500 text-xs block">Square Feet</span>
                              <p className="font-medium">{property.square_feet.toLocaleString()}</p>
                            </div>
                          )}
                        </div>

                        {/* Multiple properties indicator */}
                        {hasMultipleProperties && (
                          <div className="mt-3 bg-blue-50 p-2 rounded">
                            <p className="text-sm text-blue-700 font-medium">
                              {sameLocationProperties.length + 1} properties at this location
                            </p>
                            <div className="mt-1 max-h-32 overflow-y-auto">
                              {sameLocationProperties.map((relatedProperty) => (
                                <div 
                                  key={relatedProperty.id}
                                  className="text-xs p-1 hover:bg-blue-100 rounded cursor-pointer"
                                  onClick={() => {
                                    const originalRelatedProperty = properties.find(p => p.id === relatedProperty.id) || relatedProperty;
                                    setSelectedProperty(originalRelatedProperty);
                                  }}
                                >
                                  <div className="font-medium">{relatedProperty.name}</div>
                                  <div className="text-blue-600">{relatedProperty.num_units || relatedProperty.units} units</div>
                                </div>
                              ))}
                            </div>
                          </div>
                        )}

                        {/* Property link */}
                        <div className="mt-3 pt-3 border-t border-gray-200">
                          <a 
                            href={`/properties/${property.id}`}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-blue-600 hover:text-blue-800 text-sm flex items-center"
                          >
                            View Full Details
                            <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 ml-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                            </svg>
                          </a>
                        </div>
                      </div>
                    </Popup>
                  </Marker>
                )})}
            </CustomMarkerClusterGroup>
          )}
          
          {/* Map controllers */}
          <MapRecenter selectedProperty={selectedProperty} />
          {onBoundsChange && <MapBoundsUpdater onBoundsChange={onBoundsChange} />}
          
          {/* Add ZoomControl in top-right */}
          <ZoomControl position="topright" />
        </MapContainer>
      </div>
    </div>
  );
};

export default MapComponent;