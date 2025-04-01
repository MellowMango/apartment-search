import React from 'react';
import { Property } from '../types/property';
import { getMigrationClass } from '../config/flags';

interface PropertyListProps {
  properties: Property[];
  loading: boolean;
  selectedProperty: Property | null;
  onSelectProperty: (property: Property) => void;
  totalCount?: number;
}

const PropertyList: React.FC<PropertyListProps> = ({
  properties,
  loading,
  selectedProperty,
  onSelectProperty,
  totalCount
}) => {
  // Format price for display
  const formatPrice = (price?: number): string => {
    if (!price) return 'Price on request';
    return price >= 1000000 
      ? `$${(price / 1000000).toFixed(1)}M` 
      : `$${(price / 1000).toFixed(0)}K`;
  };

  // Format units for display
  const formatUnits = (property: Property): string => {
    const units = property.units || property.num_units;
    return units ? String(units) : 'N/A';
  };

  return (
    <div className={`h-full overflow-y-auto ${getMigrationClass('PropertyList')}`}>
      {/* Header with count */}
      <div className="sticky top-0 bg-background p-3 border-b z-10">
        <div className="flex justify-between items-center">
          <h3 className="font-semibold text-lg">Properties</h3>
          <span className="text-sm text-muted-foreground">
            {loading ? 'Loading...' : `${properties.length} of ${totalCount || 'many'} properties`}
          </span>
        </div>
      </div>

      {/* Property list */}
      {loading ? (
        <div className="flex items-center justify-center p-8">
          <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-primary"></div>
        </div>
      ) : properties.length > 0 ? (
        <ul className="divide-y">
          {properties.map((property) => (
            <li 
              key={property.id} 
              className={`hover:bg-muted/50 cursor-pointer transition-colors p-3 ${
                selectedProperty?.id === property.id ? 'bg-primary/10 border-l-4 border-primary' : ''
              }`}
              onClick={() => onSelectProperty(property)}
            >
              <div className="flex flex-col">
                <div className="flex justify-between items-start">
                  <h4 className="font-medium">{property.name || 'Unnamed Property'}</h4>
                  <span className={`text-xs px-2 py-1 rounded-full ${
                    property.status === 'Sold' 
                      ? 'bg-red-100 text-red-800' 
                      : property.status === 'Under Contract' 
                        ? 'bg-yellow-100 text-yellow-800'
                        : 'bg-green-100 text-green-800'
                  }`}>
                    {property.status || 'Available'}
                  </span>
                </div>
                <p className="text-sm text-muted-foreground truncate mt-1">{property.address}</p>
                
                <div className="grid grid-cols-2 gap-4 mt-2">
                  <div>
                    <p className="text-xs text-muted-foreground">Price</p>
                    <p className="text-sm font-semibold">{formatPrice(property.price)}</p>
                  </div>
                  <div>
                    <p className="text-xs text-muted-foreground">Units</p>
                    <p className="text-sm font-semibold">{formatUnits(property)}</p>
                  </div>
                </div>
                
                {property.year_built && (
                  <div className="mt-2">
                    <p className="text-xs text-muted-foreground">Year Built</p>
                    <p className="text-sm">{property.year_built}</p>
                  </div>
                )}
                
                {property._highlight && (
                  <div className="mt-2 bg-yellow-50 border border-yellow-200 p-2 rounded-md">
                    <p className="text-xs text-yellow-800">
                      <span className="font-medium">Note:</span> This property has coordinate or data quality issues.
                    </p>
                  </div>
                )}
              </div>
            </li>
          ))}
        </ul>
      ) : (
        <div className="flex flex-col items-center justify-center h-64 p-4 text-center">
          <svg xmlns="http://www.w3.org/2000/svg" className="h-12 w-12 text-muted-foreground/50 mb-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" />
          </svg>
          <p className="text-muted-foreground">No properties to display</p>
          <p className="text-xs text-muted-foreground mt-2">Try adjusting your filters or view a different area</p>
        </div>
      )}
    </div>
  );
};

export default PropertyList; 