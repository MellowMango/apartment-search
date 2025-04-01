# Authentication Flow

This document outlines the user authentication process and integration with Supabase Auth for the Acquire Apartments application.

## Overview

Authentication in the Acquire Apartments platform is handled through Supabase Auth, providing secure user registration, login, and account management. The system supports email/password authentication as well as OAuth providers.

## Authentication Flow Diagram

```
┌───────────┐      ┌────────────┐      ┌─────────────┐      ┌────────────┐
│           │      │            │      │             │      │            │
│  Frontend │      │   FastAPI  │      │   Supabase  │      │  SendGrid  │
│  (Next.js)│      │   Backend  │      │    Auth     │      │            │
│           │      │            │      │             │      │            │
└─────┬─────┘      └──────┬─────┘      └──────┬──────┘      └─────┬──────┘
      │                   │                    │                   │
      │                   │                    │                   │
      │  Register/Login   │                    │                   │
      │───────────────────┼────────────────────>                   │
      │                   │                    │                   │
      │                   │                    │  Send Verification│
      │                   │                    │───────────────────>
      │                   │                    │                   │
      │                   │   Auth Response    │                   │
      │<──────────────────┼────────────────────│                   │
      │                   │                    │                   │
      │   Store Token     │                    │                   │
      │───────┐           │                    │                   │
      │       │           │                    │                   │
      │<──────┘           │                    │                   │
      │                   │                    │                   │
      │  Authenticated    │                    │                   │
      │     Request       │                    │                   │
      │───────────────────>                    │                   │
      │                   │  Verify Token      │                   │
      │                   │────────────────────>                   │
      │                   │                    │                   │
      │                   │  Token Valid/Invalid                   │
      │                   │<────────────────────                   │
      │                   │                    │                   │
      │    Response       │                    │                   │
      │<──────────────────│                    │                   │
      │                   │                    │                   │
```

## Authentication Methods

### Email/Password Authentication

The primary authentication method is email and password:

1. User enters email and password in the registration form
2. Backend sends request to Supabase Auth to create a new user
3. Supabase Auth sends a verification email to the user
4. User clicks the verification link to confirm their email
5. User is redirected to the application and automatically logged in
6. JWT token is stored in local storage for subsequent requests

### Social Authentication (OAuth)

The application also supports authentication with the following OAuth providers:

- Google
- GitHub
- LinkedIn

The OAuth flow works as follows:

1. User clicks the "Sign in with [Provider]" button
2. User is redirected to the provider's authorization page
3. User grants permission to the application
4. Provider redirects back to the application with an authorization code
5. Backend exchanges the code for access and refresh tokens
6. User data is retrieved from the provider and stored in Supabase
7. User is logged in and a JWT token is stored for future requests

## Token Management

### JWT Tokens

Authentication uses JWT (JSON Web Tokens):

- **Access Token**: Short-lived token (1 hour) used for API requests
- **Refresh Token**: Long-lived token (60 days) used to obtain new access tokens

### Token Storage

Tokens are stored securely:

- **Browser**: LocalStorage or SessionStorage
- **Mobile**: Secure storage
- **Desktop**: Encrypted storage

### Token Refresh

The application automatically refreshes tokens:

1. When an access token expires, the refresh token is used to get a new one
2. If the refresh token is invalid or expired, the user is logged out
3. A background process refreshes the token before it expires

## API Authentication

### Request Authentication

All authenticated API requests include the JWT in the Authorization header:

```
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

### Server Validation

The backend validates tokens as follows:

1. Extract JWT from Authorization header
2. Verify token signature using Supabase Auth
3. Check expiration time and claims
4. If valid, process the request
5. If invalid, return 401 Unauthorized

## User Registration Process

1. User submits registration form with email, password, and name
2. Backend validates input and checks for existing users
3. If valid, creates user in Supabase Auth
4. SendGrid sends a verification email
5. User confirms email by clicking the link
6. User profile is created in the database
7. User is redirected to the application and logged in

### Registration Endpoint

```
POST /api/v1/auth/register
```

Request:
```json
{
  "email": "user@example.com",
  "password": "securepassword123",
  "name": "John Doe"
}
```

Response:
```json
{
  "user": {
    "id": "123e4567-e89b-12d3-a456-426614174000",
    "email": "user@example.com",
    "name": "John Doe",
    "created_at": "2023-01-01T00:00:00Z"
  },
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

## Login Process

1. User enters email and password
2. Backend validates credentials with Supabase Auth
3. If valid, generates a new JWT token
4. Returns user data and token to frontend
5. Frontend stores token and redirects to dashboard

### Login Endpoint

```
POST /api/v1/auth/login
```

Request:
```json
{
  "email": "user@example.com",
  "password": "securepassword123"
}
```

Response:
```json
{
  "user": {
    "id": "123e4567-e89b-12d3-a456-426614174000",
    "email": "user@example.com",
    "name": "John Doe",
    "created_at": "2023-01-01T00:00:00Z"
  },
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

## Password Reset Flow

1. User requests password reset with email address
2. Backend verifies email exists and sends reset link
3. User receives email with password reset link
4. User clicks link and enters new password
5. Backend validates token and updates password
6. User is redirected to login page

### Password Reset Endpoints

Request reset:
```
POST /api/v1/auth/reset-password
```

Request:
```json
{
  "email": "user@example.com"
}
```

Response:
```json
{
  "message": "Password reset email sent"
}
```

Confirm reset:
```
POST /api/v1/auth/reset-password/confirm
```

Request:
```json
{
  "token": "reset-token-from-email",
  "password": "new-password123"
}
```

Response:
```json
{
  "message": "Password has been reset successfully"
}
```

## Logout Process

1. User clicks logout button
2. Frontend removes JWT token from storage
3. Optional: Backend invalidates the token in Supabase
4. User is redirected to the login page

### Logout Endpoint

```
POST /api/v1/auth/logout
```

Response:
```json
{
  "message": "Logged out successfully"
}
```

## Protected Routes

In the frontend, certain routes are protected and only accessible to authenticated users:

1. React Router (or Next.js) checks for valid JWT token
2. If token exists, the protected component is rendered
3. If no token, user is redirected to login page
4. After login, user is redirected back to the original route

Example Protected Route component:

```jsx
// In components/ProtectedRoute.jsx
import { useEffect } from 'react';
import { useRouter } from 'next/router';
import { useAuth } from '../contexts/AuthContext';

const ProtectedRoute = ({ children }) => {
  const { isAuthenticated, loading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!loading && !isAuthenticated) {
      router.push({
        pathname: '/login',
        query: { returnUrl: router.asPath }
      });
    }
  }, [isAuthenticated, loading, router]);

  if (loading) {
    return <div>Loading...</div>;
  }

  return isAuthenticated ? children : null;
};

export default ProtectedRoute;
```

## Security Considerations

1. **HTTPS Only**: All authentication requests must use HTTPS
2. **CSRF Protection**: Token-based authentication helps prevent CSRF attacks
3. **Password Requirements**:
   - Minimum 8 characters
   - Mix of uppercase, lowercase, numbers, and symbols
4. **Rate Limiting**: To prevent brute force attacks
5. **Token Expiration**: Short-lived access tokens (1 hour)
6. **IP Monitoring**: Flag suspicious login attempts from unusual locations

## Implementation in Frontend

```jsx
// In contexts/AuthContext.jsx
import { createContext, useContext, useEffect, useState } from 'react';

const AuthContext = createContext();

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Check for existing token on mount
    const storedToken = localStorage.getItem('token');
    const storedUser = JSON.parse(localStorage.getItem('user'));
    
    if (storedToken && storedUser) {
      setToken(storedToken);
      setUser(storedUser);
    }
    
    setLoading(false);
  }, []);

  const login = async (email, password) => {
    try {
      const response = await fetch('/api/v1/auth/login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ email, password }),
      });
      
      const data = await response.json();
      
      if (!response.ok) {
        throw new Error(data.message || 'Login failed');
      }
      
      setUser(data.user);
      setToken(data.token);
      
      localStorage.setItem('token', data.token);
      localStorage.setItem('user', JSON.stringify(data.user));
      
      return data;
    } catch (error) {
      console.error('Login error:', error);
      throw error;
    }
  };

  const logout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    setUser(null);
    setToken(null);
  };

  const register = async (email, password, name) => {
    try {
      const response = await fetch('/api/v1/auth/register', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ email, password, name }),
      });
      
      const data = await response.json();
      
      if (!response.ok) {
        throw new Error(data.message || 'Registration failed');
      }
      
      setUser(data.user);
      setToken(data.token);
      
      localStorage.setItem('token', data.token);
      localStorage.setItem('user', JSON.stringify(data.user));
      
      return data;
    } catch (error) {
      console.error('Registration error:', error);
      throw error;
    }
  };

  const value = {
    user,
    token,
    loading,
    isAuthenticated: !!token,
    login,
    logout,
    register,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export const useAuth = () => useContext(AuthContext);
```