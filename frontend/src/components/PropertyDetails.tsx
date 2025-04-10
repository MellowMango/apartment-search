import { FC } from 'react';
import { Property } from '../types/property';

interface PropertyDetailsProps {
  property: Property;
  onClose: () => void;
}

const PropertyDetails: FC<PropertyDetailsProps> = ({ property, onClose }) => {
  // Format price as $X.XM or $XK
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
  
  // Format cap rate as percentage
  const formatCapRate = (capRate: number | undefined) => {
    if (!capRate) return 'N/A';
    return `${capRate.toFixed(2)}%`;
  };
  
  // Format date (assuming ISO string format)
  const formatDate = (dateString: string | undefined) => {
    if (!dateString) return 'N/A';
    try {
      const date = new Date(dateString);
      return date.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
      });
    } catch (e) {
      return dateString;
    }
  };
  
  // Get status styling
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
      {/* Header with close button */}
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-xl font-semibold">Property Details</h2>
        <button
          onClick={onClose}
          className="p-1 rounded-full hover:bg-gray-100 transition"
          aria-label="Close details"
        >
          <svg
            className="h-6 w-6 text-gray-500"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
            xmlns="http://www.w3.org/2000/svg"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M6 18L18 6M6 6l12 12"
            />
          </svg>
        </button>
      </div>
      
      {/* Property content - scrollable */}
      <div className="flex-grow overflow-y-auto pr-2">
        {/* Hero section */}
        <div className="mb-4">
          <div className="bg-gray-200 h-48 rounded-lg flex items-center justify-center overflow-hidden">
            {property.image_url ? (
              <img
                src={property.image_url}
                alt={property.name}
                className="w-full h-full object-cover"
              />
            ) : (
              <div className="text-center text-gray-500">
                <svg
                  className="mx-auto h-12 w-12"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                  xmlns="http://www.w3.org/2000/svg"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={1}
                    d="M3 9a2 2 0 012-2h.93a2 2 0 001.664-.89l.812-1.22A2 2 0 0110.07 4h3.86a2 2 0 011.664.89l.812 1.22A2 2 0 0018.07 7H19a2 2 0 012 2v9a2 2 0 01-2 2H5a2 2 0 01-2-2V9z"
                  />
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={1}
                    d="M15 13a3 3 0 11-6 0 3 3 0 016 0z"
                  />
                </svg>
                <p>No image available</p>
              </div>
            )}
          </div>
          <h1 className="text-2xl font-bold mt-3">{property.name}</h1>
          <p className="text-gray-600">{property.address}</p>
          <div className="mt-2">
            <span className={`inline-block px-3 py-1 rounded-full text-sm ${getStatusClass(property.status ?? '')}`}>
              {property.status}
            </span>
            {property.created_at && (
              <span className="text-sm text-gray-500 ml-2">
                Listed on {formatDate(property.created_at)}
              </span>
            )}
          </div>
          
          {property._coordinates_missing && (
            <div className="mt-2 bg-amber-50 border border-amber-200 rounded-md p-2 text-amber-700 text-sm flex items-center">
              <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-2 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
              </svg>
              <span>This property doesn't have map coordinates. It will not appear on the map but is included in the list.</span>
            </div>
          )}
          {property._geocoded && (
            <div className="mt-2 bg-blue-50 border border-blue-200 rounded-md p-2 text-blue-700 text-sm flex items-center">
              <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-2 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <span>This property's location has been estimated from its address and may not be exact.</span>
            </div>
          )}
        </div>
        
        {/* Key details */}
        <div className="grid grid-cols-2 gap-4 mb-6">
          <div className="bg-gray-50 p-3 rounded-lg">
            <div className="text-sm text-gray-500">Price</div>
            <div className="text-xl font-semibold">
              {formatPrice(property.price)}
            </div>
          </div>
          <div className="bg-gray-50 p-3 rounded-lg">
            <div className="text-sm text-gray-500">Units</div>
            <div className="text-xl font-semibold">
              {property.num_units || property.units || 'N/A'}
            </div>
          </div>
          <div className="bg-gray-50 p-3 rounded-lg">
            <div className="text-sm text-gray-500">Year Built</div>
            <div className="text-xl font-semibold">
              {property.year_built || 'N/A'}
            </div>
          </div>
          <div className="bg-gray-50 p-3 rounded-lg">
            <div className="text-sm text-gray-500">Price Per Unit</div>
            <div className="text-xl font-semibold">
              {formatPricePerUnit(property.price, property.num_units || property.units)}
            </div>
          </div>
        </div>
        
        {/* Description */}
        {property.description && (
          <div className="mb-6">
            <h3 className="text-lg font-semibold mb-2">Description</h3>
            <p className="text-gray-700 whitespace-pre-line">
              {property.description}
            </p>
          </div>
        )}
        
        {/* Financial details */}
        <div className="mb-6">
          <h3 className="text-lg font-semibold mb-2">Financial Details</h3>
          <div className="bg-gray-50 rounded-lg p-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <div className="text-sm text-gray-500">Cap Rate</div>
                <div className="font-medium">
                  {formatCapRate(property.cap_rate)}
                </div>
              </div>
              <div>
                <div className="text-sm text-gray-500">NOI</div>
                <div className="font-medium">
                  {property.noi 
                    ? `$${property.noi.toLocaleString()}` 
                    : 'N/A'}
                </div>
              </div>
              <div>
                <div className="text-sm text-gray-500">Occupancy</div>
                <div className="font-medium">
                  {property.occupancy 
                    ? `${property.occupancy}%` 
                    : 'N/A'}
                </div>
              </div>
              <div>
                <div className="text-sm text-gray-500">Avg Rent</div>
                <div className="font-medium">
                  {property.avg_rent 
                    ? `$${property.avg_rent.toLocaleString()}/mo` 
                    : 'N/A'}
                </div>
              </div>
            </div>
          </div>
        </div>
        
        {/* Property details */}
        <div className="mb-6">
          <h3 className="text-lg font-semibold mb-2">Property Details</h3>
          <div className="bg-gray-50 rounded-lg p-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <div className="text-sm text-gray-500">Type</div>
                <div className="font-medium">
                  {property.property_type || 'Multifamily'}
                </div>
              </div>
              <div>
                <div className="text-sm text-gray-500">Total Units</div>
                <div className="font-medium">
                  {property.num_units || property.units || 'N/A'}
                </div>
              </div>
              <div>
                <div className="text-sm text-gray-500">Year Built</div>
                <div className="font-medium">
                  {property.year_built || 'N/A'}
                </div>
              </div>
              <div>
                <div className="text-sm text-gray-500">Renovated</div>
                <div className="font-medium">
                  {property.year_renovated || 'N/A'}
                </div>
              </div>
              <div>
                <div className="text-sm text-gray-500">Lot Size</div>
                <div className="font-medium">
                  {property.lot_size 
                    ? `${property.lot_size.toLocaleString()} sqft` 
                    : 'N/A'}
                </div>
              </div>
              <div>
                <div className="text-sm text-gray-500">Building Size</div>
                <div className="font-medium">
                  {property.building_size 
                    ? `${property.building_size.toLocaleString()} sqft` 
                    : 'N/A'}
                </div>
              </div>
            </div>
          </div>
        </div>
        
        {/* Contact information */}
        {property.broker && (
          <div className="mb-6">
            <h3 className="text-lg font-semibold mb-2">Listing Contact</h3>
            <div className="bg-gray-50 rounded-lg p-4 flex items-center">
              <div className="bg-blue-100 rounded-full p-3 mr-4">
                <svg
                  className="h-6 w-6 text-blue-600"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                  xmlns="http://www.w3.org/2000/svg"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"
                  />
                </svg>
              </div>
              <div>
                <div className="font-medium">{property.broker.name}</div>
                {property.broker.email && (
                  <div className="text-sm text-gray-600">{property.broker.email}</div>
                )}
                {property.broker.phone && (
                  <div className="text-sm text-gray-600">{property.broker.phone}</div>
                )}
                {property.broker.brokerage && (
                  <div className="text-sm text-blue-600">{property.broker.brokerage.name}</div>
                )}
              </div>
            </div>
          </div>
        )}
      </div>
      
      {/* Action buttons */}
      <div className="pt-3 mt-3 border-t flex space-x-3">
        <button className="flex-1 py-2 px-4 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition">
          Contact Broker
        </button>
        <button className="py-2 px-4 border border-gray-300 hover:bg-gray-50 rounded-lg transition flex items-center justify-center">
          <svg
            className="h-5 w-5 text-gray-600"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
            xmlns="http://www.w3.org/2000/svg"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M5 5a2 2 0 012-2h10a2 2 0 012 2v16l-7-3.5L5 21V5z"
            />
          </svg>
        </button>
      </div>
    </div>
  );
};

export default PropertyDetails;