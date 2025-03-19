import { FC, useState } from 'react';
import { Property } from '../types/property';

interface PropertySidebarProps {
  properties: Property[];
  selectedProperty: Property | null;
  setSelectedProperty: (property: Property | null) => void;
  loading: boolean;
}

const PropertySidebar: FC<PropertySidebarProps> = ({
  properties,
  selectedProperty,
  setSelectedProperty,
  loading,
}) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  
  // Filter properties based on search term and status filter
  const filteredProperties = properties.filter(property => {
    const matchesSearch = searchTerm === '' || 
      property.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      property.address.toLowerCase().includes(searchTerm.toLowerCase());
      
    const matchesStatus = statusFilter === 'all' || 
      property.status.toLowerCase().includes(statusFilter.toLowerCase());
    
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
    if (status.toLowerCase().includes('available') || status.toLowerCase().includes('active')) {
      return 'bg-green-100 text-green-800';
    } else if (status.toLowerCase().includes('contract') || status.toLowerCase().includes('pending')) {
      return 'bg-yellow-100 text-yellow-800';
    } else if (status.toLowerCase().includes('sold')) {
      return 'bg-red-100 text-red-800';
    }
    return 'bg-gray-100 text-gray-800';
  };
  
  return (
    <div className="bg-white rounded-lg shadow p-4 flex flex-col h-[80vh] lg:h-[85vh] overflow-hidden">
      <h2 className="text-xl font-semibold mb-4">Properties</h2>
      
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
        <div className="flex space-x-2">
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
        <div className="flex-grow overflow-y-auto space-y-3 pr-2">
          {filteredProperties.map((property) => (
            <div
              key={property.id}
              className={`p-3 rounded-lg cursor-pointer transition border ${
                selectedProperty?.id === property.id
                  ? 'bg-blue-50 border-blue-500 shadow-sm'
                  : 'bg-gray-50 border-gray-200 hover:bg-gray-100'
              }`}
              onClick={() => setSelectedProperty(property)}
            >
              <div className="flex justify-between items-start">
                <h3 className="font-medium text-gray-900">{property.name}</h3>
                <span className={`px-2 py-1 rounded-full text-xs ${getStatusClass(property.status)}`}>
                  {property.status}
                </span>
              </div>
              <p className="text-sm text-gray-600 mt-1">{property.address}</p>
              <div className="grid grid-cols-2 gap-x-4 mt-2 text-sm">
                <div className="flex items-center">
                  <svg
                    className="h-4 w-4 text-gray-500 mr-1"
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
                  <span>{property.num_units || property.units} units</span>
                </div>
                {property.year_built && (
                  <div className="flex items-center">
                    <svg
                      className="h-4 w-4 text-gray-500 mr-1"
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
                    <span>Built {property.year_built}</span>
                  </div>
                )}
                {property.price && (
                  <div className="flex items-center col-span-2 mt-1">
                    <svg
                      className="h-4 w-4 text-gray-500 mr-1"
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
                    <span>{formatPrice(property.price)}</span>
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="flex-grow flex items-center justify-center text-center">
          <div>
            <svg
              className="mx-auto h-12 w-12 text-gray-400"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
              xmlns="http://www.w3.org/2000/svg"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={1}
                d="M9.172 16.172a4 4 0 015.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
              />
            </svg>
            <p className="mt-2 text-gray-500">No properties found matching your filters.</p>
            <button
              className="mt-3 text-sm text-blue-600 hover:text-blue-800"
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
      
      {/* Results counter */}
      {!loading && (
        <div className="pt-3 mt-3 border-t text-sm text-gray-500">
          Showing {filteredProperties.length} of {properties.length} properties
        </div>
      )}
    </div>
  );
};

export default PropertySidebar;