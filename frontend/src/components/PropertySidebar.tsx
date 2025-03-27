import { FC, useState } from 'react';
import { Property } from '../types/property';

// Update Property type to include optional highlight flag
declare module '../types/property' {
  interface Property {
    _highlight?: boolean;
    _coordinates_missing?: boolean;
    _geocoded?: boolean;
  }
}

interface PropertySidebarProps {
  properties: Property[];
  selectedProperty: Property | null;
  setSelectedProperty: (property: Property | null) => void;
  loading: boolean;
  sidebarState?: 'open' | 'collapsed' | 'fullscreen';
  onSidebarStateChange?: (state: 'open' | 'collapsed' | 'fullscreen') => void;
}

const PropertySidebar: FC<PropertySidebarProps> = ({
  properties,
  selectedProperty,
  setSelectedProperty,
  loading,
  sidebarState = 'open',
  onSidebarStateChange,
}) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [localSidebarState, setLocalSidebarState] = useState<'open' | 'collapsed' | 'fullscreen'>('open');
  const [compactMode, setCompactMode] = useState(true); // Default to compact mode
  
  // Use prop state if provided, otherwise use local state
  const effectiveSidebarState = sidebarState || localSidebarState;
  
  // Filter properties based on search term and status filter
  const filteredProperties = properties.filter(property => {
    const matchesSearch = searchTerm === '' || 
      property.name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      property.address?.toLowerCase().includes(searchTerm.toLowerCase());
      
    const matchesStatus = statusFilter === 'all' || 
      property.status?.toLowerCase().includes(statusFilter.toLowerCase());
    
    return matchesSearch && matchesStatus;
  });
  
  // Format price as $X.XM
  const formatPrice = (price: number | undefined) => {
    if (!price) return 'Price not available';
    if (price >= 1000000) {
      return `$${(price / 1000000).toFixed(1)}M`;
    }
    return `$${(price / 1000).toFixed(0)}K`;
  };
  
  // Format status for display
  const getStatusClass = (status: string) => {
    if (!status) return 'bg-gray-100 text-gray-800';
    if (status.toLowerCase().includes('available') || status.toLowerCase().includes('active')) {
      return 'bg-green-100 text-green-800';
    } else if (status.toLowerCase().includes('contract') || status.toLowerCase().includes('pending')) {
      return 'bg-yellow-100 text-yellow-800';
    } else if (status.toLowerCase().includes('sold')) {
      return 'bg-red-100 text-red-800';
    }
    return 'bg-gray-100 text-gray-800';
  };
  
  // Toggle sidebar state
  const toggleSidebar = () => {
    const newState = effectiveSidebarState === 'open' ? 'collapsed' : 'open';
    setLocalSidebarState(newState);
    if (onSidebarStateChange) {
      onSidebarStateChange(newState);
    }
  };

  // Toggle fullscreen mode
  const toggleFullscreen = () => {
    const newState = effectiveSidebarState === 'fullscreen' ? 'open' : 'fullscreen';
    setLocalSidebarState(newState);
    if (onSidebarStateChange) {
      onSidebarStateChange(newState);
    }
  };

  // If sidebar is collapsed, show only a narrow bar with toggle button
  if (effectiveSidebarState === 'collapsed') {
    return (
      <div className="bg-white rounded-lg shadow-md w-12 flex flex-col items-center py-4 transition-all duration-300 h-[80vh] lg:h-[85vh]">
        <button 
          onClick={toggleSidebar}
          className="p-2 rounded-full hover:bg-gray-100 mb-2"
          title="Expand sidebar"
        >
          <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-6 h-6">
            <path strokeLinecap="round" strokeLinejoin="round" d="M13.5 4.5L21 12m0 0l-7.5 7.5M21 12H3" />
          </svg>
        </button>
        <div className="flex-grow flex items-center justify-center">
          <span className="transform -rotate-90 text-gray-500 whitespace-nowrap text-sm font-medium">
            Properties List
          </span>
        </div>
      </div>
    );
  }
  
  return (
    <div className={`bg-white rounded-lg shadow-md p-4 flex flex-col transition-all duration-300 ${
      effectiveSidebarState === 'fullscreen' ? 'w-full h-[85vh]' : 'h-[80vh] lg:h-[85vh]'
    }`}>
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-xl font-semibold">Properties</h2>
        <div className="flex space-x-2">
          {/* Toggle compact mode button */}
          <button
            onClick={() => setCompactMode(!compactMode)}
            className="p-1.5 rounded-md hover:bg-gray-100"
            title={compactMode ? "Expanded view" : "Compact view"}
          >
            {compactMode ? (
              <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-5 h-5">
                <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 3.75v4.5m0-4.5h4.5m-4.5 0L9 9M3.75 20.25v-4.5m0 4.5h4.5m-4.5 0L9 15M20.25 3.75h-4.5m4.5 0v4.5m0-4.5L15 9m5.25 11.25h-4.5m4.5 0v-4.5m0 4.5L15 15" />
              </svg>
            ) : (
              <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-5 h-5">
                <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 6.75h16.5M3.75 12h16.5M12 17.25h8.25" />
              </svg>
            )}
          </button>
          
          <button 
            onClick={toggleFullscreen}
            className="p-1.5 rounded-md hover:bg-gray-100" 
            title={effectiveSidebarState === 'fullscreen' ? "Exit fullscreen" : "Fullscreen view"}
          >
            {effectiveSidebarState === 'fullscreen' ? (
              <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-5 h-5">
                <path strokeLinecap="round" strokeLinejoin="round" d="M9 9V4.5M9 9H4.5M15 9H19.5M15 9V4.5M15 14.5V19.5M15 14.5H19.5M9 14.5H4.5M9 14.5V19.5" />
              </svg>
            ) : (
              <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-5 h-5">
                <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 3.75v4.5m0-4.5h4.5m-4.5 0L9 9M3.75 20.25v-4.5m0 4.5h4.5m-4.5 0L9 15M20.25 3.75h-4.5m4.5 0v4.5m0-4.5L15 9m5.25 11.25h-4.5m4.5 0v-4.5m0 4.5L15 15" />
              </svg>
            )}
          </button>
          <button 
            onClick={toggleSidebar}
            className="p-1.5 rounded-md hover:bg-gray-100" 
            title="Collapse sidebar"
          >
            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-5 h-5">
              <path strokeLinecap="round" strokeLinejoin="round" d="M18.75 19.5l-7.5-7.5 7.5-7.5m-6 15L5.25 12l7.5-7.5" />
            </svg>
          </button>
        </div>
      </div>
      
      {/* Search and filter controls */}
      <div className="mb-4 space-y-2">
        <div className="relative">
          <input
            type="text"
            placeholder="Search properties..."
            className="w-full px-4 py-2 pr-10 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
          <svg
            className="absolute right-3 top-2.5 h-5 w-5 text-gray-400"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
            xmlns="http://www.w3.org/2000/svg"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
            />
          </svg>
        </div>
        <div className="flex flex-wrap gap-2">
          <button
            className={`px-3 py-1 rounded-full text-sm ${
              statusFilter === 'all' ? 'bg-blue-500 text-white' : 'bg-gray-200 text-gray-700'
            }`}
            onClick={() => setStatusFilter('all')}
          >
            All
          </button>
          <button
            className={`px-3 py-1 rounded-full text-sm ${
              statusFilter === 'active' ? 'bg-green-500 text-white' : 'bg-gray-200 text-gray-700'
            }`}
            onClick={() => setStatusFilter('active')}
          >
            Active
          </button>
          <button
            className={`px-3 py-1 rounded-full text-sm ${
              statusFilter === 'contract' ? 'bg-yellow-500 text-white' : 'bg-gray-200 text-gray-700'
            }`}
            onClick={() => setStatusFilter('contract')}
          >
            Under Contract
          </button>
          <button
            className={`px-3 py-1 rounded-full text-sm ${
              statusFilter === 'sold' ? 'bg-red-500 text-white' : 'bg-gray-200 text-gray-700'
            }`}
            onClick={() => setStatusFilter('sold')}
          >
            Sold
          </button>
        </div>
      </div>
      
      {/* Properties list */}
      {loading ? (
        <div className="flex-grow flex items-center justify-center">
          <div className="animate-pulse text-center">
            <div className="h-4 bg-gray-200 rounded w-3/4 mx-auto mb-2.5"></div>
            <div className="h-4 bg-gray-200 rounded w-1/2 mx-auto mb-2.5"></div>
            <div className="h-4 bg-gray-200 rounded w-5/6 mx-auto"></div>
            <p className="text-gray-500 mt-4">Loading properties...</p>
          </div>
        </div>
      ) : filteredProperties.length > 0 ? (
        <div className="flex-grow overflow-y-auto space-y-2 pr-2">
          {filteredProperties.map((property) => (
            <div
              key={property.id}
              className={`${compactMode ? 'p-2' : 'p-3'} rounded-lg cursor-pointer transition border ${
                selectedProperty?.id === property.id
                  ? 'bg-blue-50 border-blue-500 shadow-sm'
                  : property._highlight
                    ? 'bg-red-50 border-red-300 hover:bg-red-100'
                    : 'bg-gray-50 border-gray-200 hover:bg-gray-100'
              }`}
              onClick={() => setSelectedProperty(property)}
            >
              {compactMode ? (
                /* Compact card layout */
                <div className="flex flex-col">
                  <div className="flex justify-between items-start">
                    <h3 className="font-medium text-gray-900 text-sm line-clamp-1">{property.name || 'Unnamed Property'}</h3>
                    {property.status && (
                      <span className={`px-1.5 py-0.5 text-xs font-medium ml-1 ${getStatusClass(property.status)} rounded-full`}>
                        {property.status}
                      </span>
                    )}
                  </div>
                  
                  <p className="text-xs text-gray-600 mt-0.5 line-clamp-1">{property.address}</p>
                  
                  <div className="flex justify-between items-center mt-1.5 text-xs">
                    <div className="flex gap-1.5">
                      {/* Status indicators */}
                      {property._highlight && (
                        <span className="inline-flex items-center text-xs px-1 py-0.5 rounded bg-red-50 text-red-600 border border-red-200">
                          <svg xmlns="http://www.w3.org/2000/svg" className="h-3 w-3 mr-0.5" viewBox="0 0 20 20" fill="currentColor">
                            <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                          </svg>
                        </span>
                      )}
                      
                      {property._coordinates_missing && (
                        <span className="inline-flex items-center text-xs px-1 py-0.5 rounded bg-amber-50 text-amber-600 border border-amber-200">
                          <svg xmlns="http://www.w3.org/2000/svg" className="h-3 w-3" viewBox="0 0 20 20" fill="currentColor">
                            <path fillRule="evenodd" d="M5.05 4.05a7 7 0 119.9 9.9L10 18.9l-4.95-4.95a7 7 0 010-9.9zM10 11a2 2 0 100-4 2 2 0 000 4z" clipRule="evenodd" />
                          </svg>
                        </span>
                      )}
                      
                      {property._geocoded && (
                        <span className="inline-flex items-center text-xs px-1 py-0.5 rounded bg-blue-50 text-blue-600 border border-blue-200">
                          <svg xmlns="http://www.w3.org/2000/svg" className="h-3 w-3" viewBox="0 0 20 20" fill="currentColor">
                            <path fillRule="evenodd" d="M5.05 4.05a7 7 0 119.9 9.9L10 18.9l-4.95-4.95a7 7 0 010-9.9zM10 11a2 2 0 100-4 2 2 0 000 4z" clipRule="evenodd" />
                          </svg>
                        </span>
                      )}
                      
                      <span className="text-gray-600">{property.num_units || property.units || 'N/A'} units</span>
                      
                      {property.year_built && (
                        <span className="text-gray-600">{property.year_built}</span>
                      )}
                    </div>
                    
                    {property.price && (
                      <span className="font-semibold text-green-700">{formatPrice(property.price)}</span>
                    )}
                  </div>
                </div>
              ) : (
                /* Standard card layout - existing design */
                <div>
                  <div className="flex justify-between items-start">
                    <h3 className="font-medium text-gray-900 line-clamp-1">{property.name || 'Unnamed Property'}</h3>
                    {property.status && (
                      <span className={`px-2 py-0.5 rounded-full text-xs font-medium ml-2 ${getStatusClass(property.status)}`}>
                        {property.status}
                      </span>
                    )}
                  </div>
                  
                  <p className="text-sm text-gray-600 mt-1.5 mb-2 line-clamp-1">{property.address}</p>
                  
                  <div className="flex flex-wrap gap-2 mt-2 mb-1">
                    {/* Property status indicators with improved icons */}
                    {property._highlight && (
                      <div className="inline-flex items-center text-xs px-1.5 py-0.5 rounded bg-red-50 text-red-600 border border-red-200">
                        <svg xmlns="http://www.w3.org/2000/svg" className="h-3 w-3 mr-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                        </svg>
                        <span>Issue</span>
                      </div>
                    )}
                    
                    {property._coordinates_missing && (
                      <div className="inline-flex items-center text-xs px-1.5 py-0.5 rounded bg-amber-50 text-amber-600 border border-amber-200">
                        <svg xmlns="http://www.w3.org/2000/svg" className="h-3 w-3 mr-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
                        </svg>
                        <span>No location</span>
                      </div>
                    )}
                    
                    {property._geocoded && (
                      <div className="inline-flex items-center text-xs px-1.5 py-0.5 rounded bg-blue-50 text-blue-600 border border-blue-200">
                        <svg xmlns="http://www.w3.org/2000/svg" className="h-3 w-3 mr-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                        </svg>
                        <span>Located</span>
                      </div>
                    )}
                  </div>
                  
                  <div className="grid grid-cols-2 gap-x-4 mt-3 text-sm">
                    <div className="flex items-center text-gray-700">
                      <svg
                        className="h-4 w-4 text-gray-500 mr-1.5 flex-shrink-0"
                        fill="none"
                        stroke="currentColor"
                        viewBox="0 0 24 24"
                        xmlns="http://www.w3.org/2000/svg"
                      >
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth={2}
                          d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4"
                        />
                      </svg>
                      <span className="font-medium">{property.num_units || property.units || 'N/A'}</span>
                      <span className="ml-1 text-gray-500">units</span>
                    </div>
                    
                    {property.year_built && (
                      <div className="flex items-center text-gray-700">
                        <svg
                          className="h-4 w-4 text-gray-500 mr-1.5 flex-shrink-0"
                          fill="none"
                          stroke="currentColor"
                          viewBox="0 0 24 24"
                          xmlns="http://www.w3.org/2000/svg"
                        >
                          <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            strokeWidth={2}
                            d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"
                          />
                        </svg>
                        <span className="font-medium">{property.year_built}</span>
                        <span className="ml-1 text-gray-500">built</span>
                      </div>
                    )}
                  </div>
                  
                  {property.price && (
                    <div className="mt-2 pt-2 border-t border-gray-200">
                      <div className="flex items-center text-gray-800">
                        <svg
                          className="h-4 w-4 text-green-600 mr-1.5 flex-shrink-0"
                          fill="none"
                          stroke="currentColor"
                          viewBox="0 0 24 24"
                          xmlns="http://www.w3.org/2000/svg"
                        >
                          <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            strokeWidth={2}
                            d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                          />
                        </svg>
                        <span className="font-semibold text-green-700">{formatPrice(property.price)}</span>
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>
          ))}
        </div>
      ) : (
        <div className="flex-grow flex items-center justify-center text-center">
          <div>
            <svg
              className="h-16 w-16 text-gray-300 mx-auto mb-4"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
              xmlns="http://www.w3.org/2000/svg"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={1}
                d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"
              />
            </svg>
            <p className="text-gray-600">No properties found matching your criteria</p>
            <button
              className="mt-4 px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition"
              onClick={() => {
                setSearchTerm('');
                setStatusFilter('all');
              }}
            >
              Clear filters
            </button>
          </div>
        </div>
      )}
      
      {/* Show total count at bottom */}
      {!loading && filteredProperties.length > 0 && (
        <div className="text-xs text-gray-500 pt-2 mt-2 border-t border-gray-200">
          Showing {filteredProperties.length} of {properties.length} properties
        </div>
      )}
    </div>
  );
};

export default PropertySidebar;