import React, { useEffect, useState, FC, useCallback, useMemo } from 'react';
import { MapContainer, TileLayer, Marker, Popup, useMap, ZoomControl } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import { Property } from '../types/property';
import { geocodeProperties } from '../../lib/geocoding';

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
  const updateBoundsRef = useCallback(() => {
    const bounds = map.getBounds();
    onBoundsChange({
      north: bounds.getNorth(),
      south: bounds.getSouth(),
      east: bounds.getEast(),
      west: bounds.getWest(),
    });
  }, [map, onBoundsChange]);
  
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
  
  // Default center coordinates for Austin, TX
  const defaultCenter: [number, number] = [30.2672, -97.7431];
  const defaultZoom = 12;
  
  // Debug properties
  useEffect(() => {
    if (!properties || !Array.isArray(properties)) {
      console.log('No properties available');
      return;
    }
    
    console.log('Properties passed to MapComponent:', properties.length);
    
    // Log all property statuses
    const statuses = new Set(properties.map(p => p.status));
    console.log('Property statuses:', Array.from(statuses));
    
    // Detailed analysis of properties
    const analysis = {
      total: properties.length,
      hasLatLng: properties.filter(p => p.latitude && p.longitude).length,
      latLngTypeNumber: properties.filter(p => typeof p.latitude === 'number' && typeof p.longitude === 'number').length,
      zeroCoordinates: properties.filter(p => p.latitude === 0 || p.longitude === 0).length,
      fromResearch: properties.filter(p => p._coordinates_from_research).length,
      missingCoordinates: properties.filter(p => p._coordinates_missing).length,
      gridPattern: properties.filter(p => p._is_grid_pattern).length,
      testProperties: properties.filter(p => p._is_test_property).length,
    };
    console.log('Properties analysis:', analysis);
    
    // Based on filtering criteria
    const withCoordinates = properties.filter(p => 
      p.latitude && 
      p.longitude && 
      (p._coordinates_from_research || (!p._coordinates_missing && !p._is_grid_pattern)) &&
      typeof p.latitude === 'number' && 
      typeof p.longitude === 'number'
    );
    console.log('Properties with valid coordinates:', withCoordinates.length);
    
    if (withCoordinates.length > 0) {
      const sampleProperty = withCoordinates[0];
      console.log('Sample property with coordinates:', {
        id: sampleProperty.id,
        name: sampleProperty.name,
        lat: sampleProperty.latitude,
        lng: sampleProperty.longitude,
        fromResearch: sampleProperty._coordinates_from_research || false
      });
    }
  }, [properties]);

  // Geocode properties with missing coordinates
  useEffect(() => {
    if (!properties || !Array.isArray(properties)) {
      console.log('No properties available for geocoding');
      return;
    }
    
    // First, check if any properties exist with proper coordinates
    const propertiesWithValidCoordinates = properties.filter(p => 
      p.latitude && 
      p.longitude && 
      (p._coordinates_from_research || (!p._coordinates_missing && !p._is_grid_pattern)) &&
      typeof p.latitude === 'number' && 
      typeof p.longitude === 'number'
    );
    
    console.log(`MapComponent: ${propertiesWithValidCoordinates.length} of ${properties.length} properties have valid coordinates`);
    
    // Always set the processed properties first to show what we have
    setProcessedProperties(properties);
    
    // MODIFIED: Enable geocoding for properties with missing coordinates
    // even if some properties already have valid coordinates
    const propertiesToGeocode = properties.filter(p => 
      ((p._needs_geocoding || !p.latitude || !p.longitude || p._coordinates_missing || p._is_grid_pattern) && 
       (p.address || p.city)) &&
      !p._coordinates_from_research
    );
    
    console.log(`MapComponent: ${propertiesToGeocode.length} properties need geocoding`);
    
    // Only proceed if there are properties to geocode
    if (propertiesToGeocode.length > 0 && !geocodingStatus.isGeocoding) {
      // Only geocode up to 10 properties at a time to avoid API limits
      const batchToGeocode = propertiesToGeocode.slice(0, 10);
      
      setGeocodingStatus({
        isGeocoding: true,
        count: 0,
        total: batchToGeocode.length
      });
      
      console.log(`MapComponent: Geocoding batch of ${batchToGeocode.length} properties`);
      
      geocodeProperties(batchToGeocode)
        .then(geocodedProperties => {
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

  // Add helper function to get the right marker icon based on property status
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
    
    // Default marker icons based on status
    const status = property.status?.toLowerCase() || '';
    if (status === 'active' || status === 'listed') {
      return L.icon({
        iconUrl: '/icons/marker-green.png',
        iconSize: [25, 41],
        iconAnchor: [12, 41],
        popupAnchor: [1, -34],
        shadowSize: [41, 41]
      });
    } else if (status === 'contract' || status === 'under contract') {
      return L.icon({
        iconUrl: '/icons/marker-yellow.png',
        iconSize: [25, 41],
        iconAnchor: [12, 41],
        popupAnchor: [1, -34],
        shadowSize: [41, 41]
      });
    } else if (status === 'sold') {
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
    
    return properties.filter(property => {
      // We need both latitude and longitude to be defined and valid numbers
      if (!property || typeof property.latitude !== 'number' || typeof property.longitude !== 'number') {
        return false;
      }

      // Check if coordinates are zero (often a sign of placeholder data)
      if (property.latitude === 0 || property.longitude === 0) {
        return false;
      }

      // Check if coordinates are within valid ranges
      if (property.latitude < -90 || property.latitude > 90 || 
          property.longitude < -180 || property.longitude > 180) {
        return false;
      }

      // Either show properties from research or valid coordinates in Austin area
      if (property._coordinates_from_research) {
        return true;
      }

      // Filter out properties with coordinates in a grid pattern
      if (property._is_grid_pattern) {
        return false;
      }

      return true;
    });
  }, [properties]);
  
  // Check if property has valid coordinates
  const hasValidCoordinates = (property: Property): boolean => {
    if (!property) return false;

    // If the property has a verified address, it has valid coordinates
    if (property.verified_address) {
      return true;
    }
    
    // Basic type checks
    const lat = typeof property.latitude === 'number' ? property.latitude : parseFloat(property.latitude as string);
    const lng = typeof property.longitude === 'number' ? property.longitude : parseFloat(property.longitude as string);
    
    // Check for NaN, null, undefined
    if (isNaN(lat) || isNaN(lng) || lat === null || lng === null) return false;
    
    // Check for zero values (often default)
    if (lat === 0 || lng === 0) return false;
    
    // Check for reasonable coordinate ranges
    if (lat < -90 || lat > 90 || lng < -180 || lng > 180) return false;
    
    // Check for Austin default (if property state is not Texas)
    const isAustinArea = lat > 30.0 && lat < 30.5 && lng > -97.9 && lng < -97.5;
    const isTexas = property.state?.toLowerCase() === 'tx' || property.state?.toLowerCase() === 'texas';
    
    if (isAustinArea && !isTexas) {
      console.warn(`Property ${property.id} has coordinates in Austin but state is ${property.state}`);
      return false;
    }
    
    return true;
  };
  
  // Get properties with valid coordinates
  const propertiesWithCoordinates = useMemo(() => {
    if (!processedProperties || !Array.isArray(processedProperties)) {
      return [];
    }
    return processedProperties.filter(property => hasValidCoordinates(property));
  }, [processedProperties]);
  
  return (
    <div className="h-[80vh] lg:h-[85vh] rounded-lg shadow overflow-hidden relative">
      {/* Geocoding status indicator */}
      {geocodingStatus.isGeocoding && (
        <div className="absolute top-4 left-4 z-10 bg-white dark:bg-gray-800 rounded-lg shadow-md p-2 px-3 flex items-center text-sm">
          <svg className="animate-spin h-4 w-4 mr-2 text-blue-500" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
          </svg>
          <span>Locating properties on map...</span>
        </div>
      )}
      
      {/* No properties with valid coordinates message */}
      {propertiesWithCoordinates.length === 0 && (
        <div className="absolute z-10 top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 bg-white dark:bg-gray-800 p-4 rounded-lg shadow-md text-center">
          <svg xmlns="http://www.w3.org/2000/svg" className="h-8 w-8 mx-auto mb-2 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
          </svg>
          <h3 className="font-semibold text-lg">No Properties with Location Data</h3>
          <p className="text-gray-500 dark:text-gray-400 mt-1">Try adjusting your filters to find properties with valid coordinates.</p>
        </div>
      )}

      <MapContainer 
        center={defaultCenter} 
        zoom={defaultZoom}
        style={{ height: '100%', width: '100%' }}
        zoomControl={false}
      >
        <MapInitializer />
        
        {/* Use Mapbox if token is provided, otherwise use OpenStreetMap */}
        {mapboxToken ? (
          <TileLayer
            attribution='© <a href="https://www.mapbox.com/about/maps/">Mapbox</a>'
            url={`https://api.mapbox.com/styles/v1/mapbox/streets-v11/tiles/{z}/{x}/{y}?access_token=${mapboxToken}`}
          />
        ) : (
          <TileLayer
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          />
        )}
        
        {/* Add ZoomControl in top-right */}
        <ZoomControl position="topright" />
        
        {/* Map markers for properties */}
        {propertiesWithCoordinates.length > 0 && (
          <>
            {propertiesWithCoordinates.map((property) => (
              <Marker
                key={property.id}
                position={[property.latitude, property.longitude]}
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
                    <h3 className="font-bold text-lg">{property.name}</h3>
                    
                    {/* Show verified address if available, otherwise show regular address */}
                    <p className="text-gray-600">
                      {property.verified_address || property.address}
                    </p>
                    
                    {/* Add verification status indicator */}
                    {property.verified_address && (
                      <p className="text-xs text-green-600 flex items-center mt-1">
                        <svg xmlns="http://www.w3.org/2000/svg" className="h-3 w-3 mr-1" viewBox="0 0 20 20" fill="currentColor">
                          <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                        </svg>
                        Verified with Google Maps
                      </p>
                    )}
                    {!property.verified_address && property.geocoded_at && (
                      <p className="text-xs text-blue-600 flex items-center mt-1">
                        <svg xmlns="http://www.w3.org/2000/svg" className="h-3 w-3 mr-1" viewBox="0 0 20 20" fill="currentColor">
                          <path fillRule="evenodd" d="M5.05 4.05a7 7 0 119.9 9.9L10 18.9l-4.95-4.95a7 7 0 010-9.9zM10 11a2 2 0 100-4 2 2 0 000 4z" clipRule="evenodd" />
                        </svg>
                        Location estimated from address
                      </p>
                    )}
                    
                    <div className="grid grid-cols-2 gap-1 my-2">
                      <div>
                        <span className="text-gray-500 text-sm">Units:</span>
                        <p className="font-medium">{property.num_units || property.units}</p>
                      </div>
                      <div>
                        <span className="text-gray-500 text-sm">Year Built:</span>
                        <p className="font-medium">{property.year_built || 'N/A'}</p>
                      </div>
                      <div>
                        <span className="text-gray-500 text-sm">Price:</span>
                        <p className="font-medium">{formatPrice(property.price)}</p>
                      </div>
                      <div>
                        <span className="text-gray-500 text-sm">Per Unit:</span>
                        <p className="font-medium">{formatPricePerUnit(property.price, property.num_units || property.units)}</p>
                      </div>
                    </div>
                    <div className="mt-2 pt-2 border-t">
                      <span className={`px-2 py-1 rounded-full text-xs ${
                        property.status === 'available' || property.status === 'Actively Marketed'
                          ? 'bg-green-100 text-green-800' 
                          : property.status === 'under_contract' || property.status === 'Under Contract'
                          ? 'bg-yellow-100 text-yellow-800' 
                          : 'bg-red-100 text-red-800'
                      }`}>
                        {property.status}
                      </span>
                    </div>
                    <button 
                      className="mt-3 w-full py-1 px-2 bg-blue-600 hover:bg-blue-700 text-white rounded text-sm transition"
                      onClick={() => {
                        const originalProperty = properties.find(p => p.id === property.id) || property;
                        setSelectedProperty(originalProperty);
                      }}
                    >
                      View Details
                    </button>
                  </div>
                </Popup>
              </Marker>
            ))}
          </>
        )}
        
        {/* Map controllers */}
        <MapRecenter selectedProperty={selectedProperty} />
        {onBoundsChange && <MapBoundsUpdater onBoundsChange={onBoundsChange} />}
      </MapContainer>
    </div>
  );
};

export default MapComponent;