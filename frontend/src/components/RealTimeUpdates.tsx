/**
 * RealTimeUpdates.tsx
 * Component for handling real-time property updates via Socket.IO
 * 
 * Features:
 * - Connects to Socket.IO server
 * - Listens for property-updated and property-created events
 * - Updates property data in real-time
 * - Shows toast notifications for important changes
 */

import { useEffect, useState, FC, useCallback } from 'react';
import { io, Socket } from 'socket.io-client';
import { Property } from '../types/property';
import { useTheme } from '../contexts/ThemeContext';

interface RealTimeUpdatesProps {
  onPropertyUpdate: (property: Property) => void;
  onPropertyCreate: (property: Property) => void;
}

const RealTimeUpdates: FC<RealTimeUpdatesProps> = ({
  onPropertyUpdate,
  onPropertyCreate,
}) => {
  const [socket, setSocket] = useState<Socket | null>(null);
  const [connected, setConnected] = useState(false);
  const [notifications, setNotifications] = useState<Array<{id: string, message: string, type: string}>>([]);
  const { isDarkMode } = useTheme();
  
  // Define notification helper function
  const addNotification = useCallback((message: string, type: string) => {
    const id = Math.random().toString(36).substring(2, 9);
    setNotifications(prev => [...prev, { id, message, type }]);
    
    // Auto-remove notification after 5 seconds
    setTimeout(() => {
      setNotifications(prev => prev.filter(notification => notification.id !== id));
    }, 5000);
  }, []);
  
  // Connect to Socket.IO server on component mount
  useEffect(() => {
    const socketUrl = process.env.NEXT_PUBLIC_SOCKET_URL || 'http://localhost:5000';
    
    // Use try-catch to prevent unhandled errors from socket connection
    try {
      const socketInstance = io(socketUrl, {
        transports: ['websocket', 'polling'], // Try websocket first, fallback to polling
        autoConnect: true,
        reconnection: true,
        reconnectionAttempts: 5,
        reconnectionDelay: 1000,
        timeout: 5000, // Increase timeout to 5 seconds
      });
      
      // Add mock events in development environment
      if (process.env.NODE_ENV === 'development') {
        console.log('Setting up mock Socket.IO events for development');
        
        // Simulate connection success
        setTimeout(() => {
          if (!socketInstance.connected) {
            console.log('Using simulated Socket.IO connection for development');
            setConnected(true);
            
            // Simulate periodic property updates for testing
            const mockInterval = setInterval(() => {
              // Only simulate if we're still in dev mode and socket isn't actually connected
              if (process.env.NODE_ENV === 'development' && !socketInstance.connected) {
                if (Math.random() > 0.8) { // 20% chance of a mock update
                  const mockProperty = {
                    id: `mock-${Math.floor(Math.random() * 1000)}`,
                    name: `Test Property ${Math.floor(Math.random() * 100)}`,
                    address: '123 Test Street, Austin, TX',
                    status: ['Available', 'Under Contract', 'Sold'][Math.floor(Math.random() * 3)],
                    price: Math.floor(Math.random() * 5000000) + 1000000,
                    latitude: 30.2672 + (Math.random() * 0.1 - 0.05),
                    longitude: -97.7431 + (Math.random() * 0.1 - 0.05),
                    city: 'Austin',
                    state: 'TX'
                  } as Property;
                  
                  // Simulate random property updates or creations
                  if (Math.random() > 0.5) {
                    console.log('MOCK: Property updated event');
                    onPropertyUpdate(mockProperty);
                    addNotification(`Property "${mockProperty.name}" has been updated (TEST)`, 'update');
                  } else {
                    console.log('MOCK: Property created event');
                    onPropertyCreate(mockProperty);
                    addNotification(`New property "${mockProperty.name}" has been added (TEST)`, 'create');
                  }
                }
              }
            }, 30000); // Every 30 seconds
            
            return () => clearInterval(mockInterval);
          }
        }, 3000);
      }
      
      setSocket(socketInstance);
      
      // Clean up socket connection on unmount
      return () => {
        if (socketInstance) {
          socketInstance.disconnect();
        }
      };
    } catch (error) {
      console.error('Error setting up Socket.IO:', error);
      // Continue without crashing - app can still function without real-time updates
      setConnected(false);
    }
  }, [onPropertyUpdate, onPropertyCreate, addNotification]);
  
  // Set up event listeners once socket is created
  useEffect(() => {
    if (!socket) return;
    
    // Connection status events
    socket.on('connect', () => {
      console.log('Connected to Socket.IO server');
      setConnected(true);
    });
    
    socket.on('disconnect', () => {
      console.log('Disconnected from Socket.IO server');
      setConnected(false);
    });
    
    socket.on('connect_error', (error) => {
      console.error('Socket connection error:', error);
      setConnected(false);
    });
    
    // Property update events
    socket.on('property-updated', (data: Property) => {
      console.log('Property updated:', data);
      onPropertyUpdate(data);
      
      // Add notification
      addNotification(`Property "${data.name}" has been updated`, 'update');
    });
    
    socket.on('property-created', (data: Property) => {
      console.log('New property:', data);
      onPropertyCreate(data);
      
      // Add notification
      addNotification(`New property "${data.name}" has been added`, 'create');
    });
    
    // Clean up event listeners
    return () => {
      socket.off('connect');
      socket.off('disconnect');
      socket.off('connect_error');
      socket.off('property-updated');
      socket.off('property-created');
    };
  }, [socket, onPropertyUpdate, onPropertyCreate, addNotification]);
  
  // Remove a specific notification
  const removeNotification = (id: string) => {
    setNotifications(prev => prev.filter(notification => notification.id !== id));
  };
  
  // If not showing any notifications or connection status, render null
  if (notifications.length === 0 && !connected) {
    return null;
  }
  
  return (
    <div className="fixed bottom-5 right-5 z-50 flex flex-col space-y-2">
      {/* Connection status indicator */}
      {connected && (
        <div className={`px-3 py-2 rounded-full shadow-lg text-xs font-medium inline-flex items-center ${
          isDarkMode ? 'bg-gray-800 text-green-400' : 'bg-white text-green-600'
        }`}>
          <span className="relative flex h-2 w-2 mr-2">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"></span>
            <span className="relative inline-flex rounded-full h-2 w-2 bg-green-500"></span>
          </span>
          Real-time updates active
        </div>
      )}
      
      {/* Notifications */}
      {notifications.map(({ id, message, type }) => (
        <div 
          key={id}
          className={`px-4 py-3 rounded-lg shadow-lg max-w-md flex items-start justify-between transition-all duration-300 ease-in-out ${
            isDarkMode 
              ? 'bg-gray-800 text-white' 
              : 'bg-white text-gray-800'
          } ${
            type === 'update' 
              ? isDarkMode ? 'border-l-4 border-blue-500' : 'border-l-4 border-blue-600'
              : isDarkMode ? 'border-l-4 border-green-500' : 'border-l-4 border-green-600'
          }`}
        >
          <div className="flex items-center">
            <span className={`flex-shrink-0 h-5 w-5 mr-2 ${
              type === 'update' 
                ? 'text-blue-500' 
                : 'text-green-500'
            }`}>
              {type === 'update' ? (
                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
                  <path d="M13.586 3.586a2 2 0 112.828 2.828l-.793.793-2.828-2.828.793-.793zM11.379 5.793L3 14.172V17h2.828l8.38-8.379-2.83-2.828z" />
                </svg>
              ) : (
                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm1-11a1 1 0 10-2 0v2H7a1 1 0 100 2h2v2a1 1 0 102 0v-2h2a1 1 0 100-2h-2V7z" clipRule="evenodd" />
                </svg>
              )}
            </span>
            <p className="text-sm">{message}</p>
          </div>
          <button
            type="button"
            className="ml-4 flex-shrink-0 text-gray-400 hover:text-gray-500"
            onClick={() => removeNotification(id)}
          >
            <svg className="h-4 w-4" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
              <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
            </svg>
          </button>
        </div>
      ))}
    </div>
  );
};

export default RealTimeUpdates;