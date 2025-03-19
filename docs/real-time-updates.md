# Real-Time Updates Flow

This document describes the architecture and flow for real-time property updates in the Acquire Apartments application.

## Overview

The real-time update system allows users to receive instant notifications about property changes without needing to refresh the page. This includes:

- New property listings
- Price changes
- Status updates (available → pending → sold)
- Other property detail updates

## Architecture

The real-time updates are built using a Socket.IO server integrated with FastAPI and the frontend.

```
┌─────────────┐         ┌─────────────┐         ┌─────────────┐
│             │         │             │         │             │
│  Supabase   │ ──────> │   FastAPI   │ ──────> │  Frontend   │
│  Database   │         │  Socket.IO  │         │  (Next.js)  │
│             │         │             │         │             │
└─────────────┘         └─────────────┘         └─────────────┘
       │                      ▲                       │
       │                      │                       │
       │                      │                       │
       │                 ┌────┴────┐                  │
       └────────────────>│  Celery │<─────────────────┘
                         │ Workers │
                         └─────────┘
```

## Data Flow

1. **Database Changes**:
   - When a property is created, updated, or deleted in Supabase
   - Supabase database triggers capture these changes

2. **Change Processing**:
   - Celery workers process database changes
   - Change data is formatted for socket broadcasting
   - Relevant users are identified for targeted notifications

3. **Socket.IO Broadcasting**:
   - The FastAPI Socket.IO server broadcasts events to connected clients
   - Events include property updates and new property listings

4. **Frontend Handling**:
   - The frontend listens for socket events
   - On receiving events, it updates the React state
   - UI components re-render with the updated data
   - Notification alerts are shown for important changes

## Socket.IO Events

### Property Updated Event

When a property is updated:

```json
{
  "event": "property-updated",
  "data": {
    "property_id": "123e4567-e89b-12d3-a456-426614174000",
    "changes": {
      "status": {
        "old": "available",
        "new": "pending"
      },
      "price": {
        "old": 10000000,
        "new": 9800000
      }
    },
    "updated_at": "2023-02-01T00:00:00Z"
  }
}
```

### New Property Event

When a new property is added:

```json
{
  "event": "property-created",
  "data": {
    "property_id": "123e4567-e89b-12d3-a456-426614174005",
    "name": "Oak View Apartments",
    "city": "Austin",
    "state": "TX",
    "price": 12500000,
    "units": 120,
    "latitude": 30.2742,
    "longitude": -97.7400,
    "created_at": "2023-02-01T00:00:00Z"
  }
}
```

### Property Deleted Event

When a property is removed:

```json
{
  "event": "property-deleted",
  "data": {
    "property_id": "123e4567-e89b-12d3-a456-426614174000",
    "deleted_at": "2023-02-01T00:00:00Z"
  }
}
```

## Implementation Details

### Backend Implementation

The Socket.IO server is integrated with FastAPI:

```python
# In app/main.py
import socketio
from fastapi import FastAPI

app = FastAPI()
sio = socketio.AsyncServer(async_mode='asgi', cors_allowed_origins=['*'])
socket_app = socketio.ASGIApp(sio, app)

@sio.event
async def connect(sid, environ):
    print(f"Client connected: {sid}")

@sio.event
async def disconnect(sid):
    print(f"Client disconnected: {sid}")
```

Broadcasting events from Celery workers:

```python
# In app/workers/tasks/property_sync.py
from app.core.celery_app import celery_app
from app.services.socketio_service import emit_property_update

@celery_app.task
def process_property_update(property_id, changes):
    # Process the update
    # ...
    
    # Emit the update to connected clients
    emit_property_update(property_id, changes)
```

### Frontend Implementation

Socket.IO client setup in Next.js:

```javascript
// In contexts/SocketContext.js
import { createContext, useContext, useEffect, useState } from 'react';
import { io } from 'socket.io-client';

const SocketContext = createContext();

export const SocketProvider = ({ children }) => {
  const [socket, setSocket] = useState(null);
  const [isConnected, setIsConnected] = useState(false);

  useEffect(() => {
    // Initialize Socket.IO connection
    const socketInstance = io(process.env.NEXT_PUBLIC_API_URL, {
      path: '/socket.io',
      autoConnect: true,
    });

    // Connection events
    socketInstance.on('connect', () => {
      console.log('Socket.IO connected');
      setIsConnected(true);
    });

    socketInstance.on('disconnect', () => {
      console.log('Socket.IO disconnected');
      setIsConnected(false);
    });

    setSocket(socketInstance);

    // Cleanup on unmount
    return () => {
      socketInstance.disconnect();
    };
  }, []);

  return (
    <SocketContext.Provider value={{ socket, isConnected }}>
      {children}
    </SocketContext.Provider>
  );
};

export const useSocket = () => useContext(SocketContext);
```

Handling property updates:

```javascript
// In contexts/PropertyContext.js
import { createContext, useContext, useEffect, useReducer } from 'react';
import { useSocket } from './SocketContext';

// Initial state and reducer
// ...

export const PropertyProvider = ({ children }) => {
  const [state, dispatch] = useReducer(propertyReducer, initialState);
  const { socket, isConnected } = useSocket();

  useEffect(() => {
    if (socket && isConnected) {
      // Listen for property updates
      socket.on('property-updated', (event) => {
        dispatch({
          type: 'PROPERTY_UPDATED',
          payload: event.data
        });
      });

      // Listen for new properties
      socket.on('property-created', (event) => {
        dispatch({
          type: 'PROPERTY_CREATED',
          payload: event.data
        });
      });

      // Listen for property deletions
      socket.on('property-deleted', (event) => {
        dispatch({
          type: 'PROPERTY_DELETED',
          payload: event.data
        });
      });

      // Cleanup listeners on unmount
      return () => {
        socket.off('property-updated');
        socket.off('property-created');
        socket.off('property-deleted');
      };
    }
  }, [socket, isConnected]);

  // Rest of the component...
};
```

## Testing Real-Time Updates

To verify the real-time update flow:

1. Start the backend server and Celery workers
2. Connect multiple browser clients to the application
3. Make changes to property data in the database
4. Verify that updates are broadcasted to all connected clients
5. Check that the UI updates correctly with the new data
6. Verify that notifications appear for important changes

## Performance Considerations

- Socket.IO uses WebSockets with fallback to long polling
- Events are lightweight JSON payloads to minimize bandwidth
- For performance with many clients, consider:
  - Using Redis for Socket.IO adapter
  - Implementing room-based filtering
  - Batching updates when multiple changes occur simultaneously