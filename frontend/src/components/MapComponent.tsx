import { useEffect, useState, FC } from 'react';
import { MapContainer, TileLayer, Marker, Popup, useMap, ZoomControl } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import { Property } from '../types/property';

// Component to handle map initialization effects
const MapInitializer: FC = () => {
  useEffect(() => {
    // Fix Leaflet marker icon issue in Next.js
    delete L.Icon.Default.prototype._getIconUrl;
    L.Icon.Default.mergeOptions({
      iconRetinaUrl: 'https://unpkg.com/leaflet@1.7.1/dist/images/marker-icon-2x.png',
      iconUrl: 'https://unpkg.com/leaflet@1.7.1/dist/images/marker-icon.png',
      shadowUrl: 'https://unpkg.com/leaflet@1.7.1/dist/images/marker-shadow.png',
    });
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
    if (selectedProperty && selectedProperty.latitude && selectedProperty.longitude) {
      map.setView(
        [selectedProperty.latitude, selectedProperty.longitude],
        15,
        { animate: true }
      );
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
  
  useEffect(() => {
    const updateBounds = () => {
      const bounds = map.getBounds();
      onBoundsChange({
        north: bounds.getNorth(),
        south: bounds.getSouth(),
        east: bounds.getEast(),
        west: bounds.getWest(),
      });
    };
    
    // Initial bounds update
    updateBounds();
    
    // Add event listeners
    map.on('moveend', updateBounds);
    map.on('zoomend', updateBounds);
    
    // Cleanup listeners
    return () => {
      map.off('moveend', updateBounds);
      map.off('zoomend', updateBounds);
    };
  }, [map, onBoundsChange]);
  
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
  // Default center coordinates for Austin, TX
  const defaultCenter: [number, number] = [30.2672, -97.7431];
  const defaultZoom = 12;
  
  // Get marker icon based on property status
  const getMarkerIcon = (status: string) => {
    return statusIcons[status] || statusIcons.default;
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
  
  return (
    <div className="h-[80vh] lg:h-[85vh] rounded-lg shadow overflow-hidden">
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
        {properties.map(property => (
          property.latitude && property.longitude ? (
            <Marker
              key={property.id}
              position={[property.latitude, property.longitude]}
              icon={getMarkerIcon(property.status)}
              eventHandlers={{
                click: () => {
                  setSelectedProperty(property);
                },
              }}
            >
              <Popup>
                <div className="min-w-[220px]">
                  <h3 className="font-bold text-lg">{property.name}</h3>
                  <p className="text-gray-600">{property.address}</p>
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
                    onClick={() => setSelectedProperty(property)}
                  >
                    View Details
                  </button>
                </div>
              </Popup>
            </Marker>
          ) : null
        ))}
        
        {/* Map controllers */}
        <MapRecenter selectedProperty={selectedProperty} />
        {onBoundsChange && <MapBoundsUpdater onBoundsChange={onBoundsChange} />}
      </MapContainer>
    </div>
  );
};

export default MapComponent;