import { useEffect, useState, FC } from 'react';
import { MapContainer, TileLayer, Marker, Popup, useMap } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';

// Fix Leaflet marker icon issue in Next.js
// This is needed because Next.js doesn't handle Leaflet's assets correctly
useEffect(() => {
  delete L.Icon.Default.prototype._getIconUrl;
  L.Icon.Default.mergeOptions({
    iconRetinaUrl: '/images/marker-icon-2x.png',
    iconUrl: '/images/marker-icon.png',
    shadowUrl: '/images/marker-shadow.png',
  });
}, []);

// Custom marker icons for different property statuses
const activeIcon = new L.Icon({
  iconUrl: '/images/marker-icon-green.png',
  shadowUrl: '/images/marker-shadow.png',
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
  shadowSize: [41, 41]
});

const underContractIcon = new L.Icon({
  iconUrl: '/images/marker-icon-yellow.png',
  shadowUrl: '/images/marker-shadow.png',
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
  shadowSize: [41, 41]
});

const soldIcon = new L.Icon({
  iconUrl: '/images/marker-icon-red.png',
  shadowUrl: '/images/marker-shadow.png',
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
  shadowSize: [41, 41]
});

interface Property {
  id: string;
  name: string;
  address: string;
  latitude: number;
  longitude: number;
  num_units: number;
  year_built?: number;
  status: string;
  brokerage_id: string;
}

interface MapComponentProps {
  properties: Property[];
  selectedProperty: Property | null;
  setSelectedProperty: (property: Property | null) => void;
}

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

const MapComponent: FC<MapComponentProps> = ({ 
  properties, 
  selectedProperty, 
  setSelectedProperty 
}) => {
  // Default center coordinates for Austin, TX
  const defaultCenter: [number, number] = [30.2672, -97.7431];
  const defaultZoom = 12;
  
  // Get marker icon based on property status
  const getMarkerIcon = (status: string) => {
    switch (status) {
      case 'Actively Marketed':
        return activeIcon;
      case 'Under Contract':
        return underContractIcon;
      case 'Sold':
        return soldIcon;
      default:
        return new L.Icon.Default();
    }
  };
  
  return (
    <div className="h-[70vh] rounded shadow overflow-hidden">
      <MapContainer 
        center={defaultCenter} 
        zoom={defaultZoom} 
        style={{ height: '100%', width: '100%' }}
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        
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
                <div>
                  <h3 className="font-bold">{property.name}</h3>
                  <p>{property.address}</p>
                  <p>{property.num_units} units</p>
                  {property.year_built && <p>Built: {property.year_built}</p>}
                  <p className="mt-2">Status: {property.status}</p>
                </div>
              </Popup>
            </Marker>
          ) : null
        ))}
        
        <MapRecenter selectedProperty={selectedProperty} />
      </MapContainer>
    </div>
  );
};

export default MapComponent; 