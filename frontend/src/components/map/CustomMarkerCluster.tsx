import React from 'react';
// @ts-ignore - to avoid TypeScript errors
import MarkerClusterGroup from 'react-leaflet-cluster';
import L from 'leaflet';

// This is a wrapper component around react-leaflet-cluster
// We've patched the original module to remove CSS imports
// The CSS is loaded in _app.js globally instead
const CustomMarkerClusterGroup: React.FC<any> = (props) => {
  // Enhanced props for better clustering behavior
  const enhancedProps = {
    ...props,
    // Revert to default clustering radius for better grouping of nearby properties
    maxClusterRadius: 40,
    // Ensure clusters expand nicely when clicked
    spiderfyOnMaxZoom: true,
    // Makes the spider legs longer for better separation when many markers are at same point
    spiderfyDistanceMultiplier: 3,
    // This ensures properties at exact same coordinates are accessible when expanded
    zoomToBoundsOnClick: true,
    // Custom icon creation for clusters
    iconCreateFunction: (cluster: any) => {
      const count = cluster.getChildCount();
      let className = 'marker-cluster ';
      
      // Add different classes based on the number of markers in the cluster
      if (count < 5) {
        className += 'marker-cluster-small';
      } else if (count < 15) {
        className += 'marker-cluster-medium';
      } else {
        className += 'marker-cluster-large';
      }
      
      return L.divIcon({
        html: `<div><span>${count}</span></div>`,
        className: className,
        iconSize: L.point(40, 40)
      });
    }
  };
  
  return <MarkerClusterGroup {...enhancedProps} />;
};

export default CustomMarkerClusterGroup; 