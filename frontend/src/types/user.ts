export interface User {
  id: string;
  email?: string;
  app_metadata?: {
    provider?: string;
    [key: string]: any;
  };
  user_metadata?: {
    name?: string;
    avatar_url?: string;
    [key: string]: any;
  };
  created_at?: string;
  updated_at?: string;
  aud?: string;
  role?: string;
  [key: string]: any;
}

export interface Session {
  access_token: string;
  refresh_token?: string;
  expires_at?: number;
  expires_in?: number;
  token_type?: string;
  user?: User;
}

export interface AuthResponse {
  data: {
    user?: User | null;
    session?: Session | null;
    url?: string;
    provider?: string;
  } | null;
  error: Error | null;
}

export interface UserCredentials {
  email: string;
  password: string;
}

export interface PasswordResetRequest {
  email: string;
}

export interface PasswordUpdateRequest {
  password: string;
}

export interface AuthProviderProps {
  children: React.ReactNode;
} 